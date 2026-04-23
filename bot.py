import telebot
import os
import google.generativeai as genai
from supabase import create_client, Client

# Ambil semua token dari Environment Variable Render
TOKEN = os.environ.get("8672136890:AAFkWjeklRxVGQE_90WWJfr2EG8H6e9DFcI")
GEMINI_KEY = os.environ.get("AIzaSyBnnWQCtq51Kn0R_0SddCQE8F5K2rggkrc")
SUPABASE_URL = os.environ.get("https://csphdmiblaaiajgoirxb.supabase.co/rest/v1/")
SUPABASE_KEY = os.environ.get("sb_publishable_TUENSpcOi2w2AIfTh7B2iQ_rwg29ZnE")

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    nama = message.from_user.first_name

    # Cek user udah ada di db belum
    cek = supabase.table('users').select("*").eq('id', user_id).execute()
    if not cek.data:
        supabase.table('users').insert({"id": user_id, "first_name": nama}).execute()
        bot.reply_to(message, f"Halo {nama}! Aku bot AI pake Gemini. Langsung tanya aja ya.")
    else:
        bot.reply_to(message, f"Selamat datang lagi {nama}! Tanya apa hari ini?")

# /poin
@bot.message_handler(commands=['poin'])
def cek_poin(message):
    user_id = message.from_user.id
    data = supabase.table('users').select("poin").eq('id', user_id).execute()
    poin = data.data[0]['poin'] if data.data else 0
    bot.reply_to(message, f"Poin kamu: {poin} ✨")

# Semua chat masuk ke Gemini
@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    try:
        user_id = message.from_user.id
        bot.send_chat_action(message.chat.id, 'typing')

        # Kirim ke Gemini
        respon = model.generate_content(message.text)

        # Tambah 1 poin tiap nanya
        supabase.table('users').update({"poin": supabase.table('users').select("poin").eq('id', user_id).execute().data[0]['poin'] + 1}).eq('id', user_id).execute()

        bot.reply_to(message, respon.text)
    except Exception as e:
        print(e)
        bot.reply_to(message, "Waduh AI-nya lagi error. Coba lagi 1 menit ya.")

print("Bot AI + Supabase jalan di Render...")
bot.infinity_polling()