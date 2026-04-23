# Copyright (c) 2026 Zyura</>
# All rights reserved.

import os
import sys
import telebot
import httpx
from google import genai

# ===== ENV =====
TOKEN = os.environ.get("BOT_TOKEN", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

missing = [v for v, k in {
    "BOT_TOKEN": TOKEN,
    "GEMINI_API_KEY": GEMINI_KEY,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_KEY": SUPABASE_KEY
}.items() if not k]

if missing:
    raise SystemExit(f"ENV KOSONG: {', '.join(missing)}. Set di Railway Variables")

bot = telebot.TeleBot(TOKEN)
client = genai.Client(api_key=GEMINI_KEY)
SB_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}
COPYRIGHT = "\n\n© 2026 Zyura</>"

# ===== SUPABASE HELPER =====
def sb_get_user(user_id):
    url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}&select=*"
    r = httpx.get(url, headers=SB_HEADERS, timeout=10)
    return r.json() if r.status_code == 200 else []

def sb_create_user(user_id, nama):
    url = f"{SUPABASE_URL}/rest/v1/users"
    data = {"id": user_id, "first_name": nama, "poin": 0}
    r = httpx.post(url, headers=SB_HEADERS, json=data, timeout=10)
    return r.status_code == 201

def sb_add_poin(user_id, tambah):
    user = sb_get_user(user_id)
    if not user: return
    poin_baru = user[0]['poin'] + tambah
    url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
    httpx.patch(url, headers=SB_HEADERS, json={"poin": poin_baru}, timeout=10)

# ===== BOT HANDLER =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    nama = message.from_user.first_name
    if not sb_get_user(user_id):
        sb_create_user(user_id, nama)
        bot.reply_to(message, f"Halo {nama}! Aku bot AI pake Gemini 2.0 Flash. Langsung tanya aja ya.{COPYRIGHT}")
    else:
        bot.reply_to(message, f"Selamat datang lagi {nama}! Tanya apa hari ini?{COPYRIGHT}")

@bot.message_handler(commands=['poin'])
def cek_poin(message):
    user = sb_get_user(message.from_user.id)
    if user:
        bot.reply_to(message, f"Poin kamu: {user[0]['poin']}{COPYRIGHT}")
    else:
        bot.reply_to(message, f"Kamu belum terdaftar. /start dulu{COPYRIGHT}")

@bot.message_handler(commands=['models'])
def list_models(message):
    try:
        models = [m.name.replace('models/', '') for m in client.models.list()]
        text = "Model aktif:\n" + "\n".join(models)
        bot.reply_to(message, text[:4000])
    except Exception as e:
        bot.reply_to(message, f"Error: {e}{COPYRIGHT}")

@bot.message_handler(func=lambda msg: True)
def chat_ai(message):
    try:
        sb_add_poin(message.from_user.id, 1)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message.text
        )
        bot.reply_to(message, response.text + COPYRIGHT)
    except Exception as e:
        print(f"ERROR GEMINI: {e}")
        bot.reply_to(message, f"Error Gemini: {e}{COPYRIGHT}")

print("Bot AI jalan di Railway...")
bot.infinity_polling()
