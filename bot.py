# Copyright (c) 2026 Zyura</>
# All rights reserved.

import telebot
import os
from groq import Groq
from supabase import create_client, Client

TOKEN = os.environ.get("BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY") # ganti nama env
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

bot = telebot.TeleBot(TOKEN)
client = Groq(api_key=GROQ_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

COPYRIGHT = "\n\n© 2026 Zyura</>"

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    nama = message.from_user.first_name
    cek = supabase.table('users').select("*").eq('id', user_id).execute()
    if not cek.data:
        supabase.table('users').insert({"id": user_id, "first_name": nama, "poin": 0}).execute()
        bot.reply_to(message, f"Halo {nama}! Aku bot AI pake Groq Llama. Langsung tanya aja ya.{COPYRIGHT}")
    else:
        bot.reply_to(message, f"Selamat datang lagi {nama}! Tanya apa hari ini?{COPYRIGHT}")

@bot.message_handler(commands=['poin'])
def cek_poin(message):
    user_id = message.from_user.id
    data = supabase.table('users').select("poin").eq('id', user_id).execute()
    poin = data.data[0]['poin'] if data.data else 0
    bot.reply_to(message, f"Poin kamu: {poin} ✨{COPYRIGHT}")

@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    try:
        user_id = message.from_user.id
        bot.send_chat_action(message.chat.id, 'typing')
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant", # paling kenceng & gratis
        )
        response = chat_completion.choices[0].message.content

        user_data = supabase.table('users').select("poin").eq('id', user_id).execute()
        if user_data.data:
            poin_baru = user_data.data[0]['poin'] + 1
            supabase.table('users').update({"poin": poin_baru}).eq('id', user_id).execute()
        bot.reply_to(message, response + COPYRIGHT)
    except Exception as e:
        print(f"GROQ ERROR: {e}")
        bot.reply_to(message, f"Waduh AI-nya lagi error.{COPYRIGHT}")

print("Bot AI jalan di Railway...")
bot.remove_webhook()
bot.infinity_polling(skip_pending=True)
