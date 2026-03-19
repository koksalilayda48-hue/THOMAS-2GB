import os
import json
import time
from datetime import date
import telebot
import threading
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

KANAL_LINK = "@bedavakampanyalarorg"
GRUP_LINK = "vipgrubum"
DAILY_ODUL = 2

# ---------------- WEB (KEEP ALIVE) ----------------
@app.route('/')
def home():
    return "Bot aktif!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# ---------------- DATA ----------------
def load_data():
    try:
        with open("ref.json", "r") as f:
            return json.load(f)
    except:
        return {"refs": {}, "users": {}, "daily_refs": {}, "joined": []}

def save_data():
    with open("ref.json", "w") as f:
        json.dump(DATA, f)

DATA = load_data()

# ---------------- REFERANS ----------------
def add_ref(ref_id, new_user_id, username=None):
    ref_id = str(ref_id)
    new_user_id = str(new_user_id)

    if new_user_id in DATA["joined"]:
        return

    DATA["joined"].append(new_user_id)
    DATA["refs"][ref_id] = DATA["refs"].get(ref_id, 0) + 1

    today = date.today().isoformat()
    if today not in DATA["daily_refs"]:
        DATA["daily_refs"][today] = {}

    DATA["daily_refs"][today][ref_id] = DATA["daily_refs"][today].get(ref_id, 0) + 1

    if username:
        DATA["users"][ref_id] = username

    keys = sorted(DATA["daily_refs"].keys())
    if len(keys) > 4:
        del DATA["daily_refs"][keys[0]]

    save_data()

# ---------------- KONTROL ----------------
def check_join(user_id):
    try:
        k = bot.get_chat_member(KANAL_LINK, user_id)
        g = bot.get_chat_member(GRUP_LINK, user_id)
        return k.status in ["member", "creator", "administrator"] and g.status in ["member", "creator", "administrator"]
    except:
        return False

def get_ref_link(user_id):
    return f"https://t.me/{bot.get_me().username}?start={user_id}"

# ---------------- START ----------------
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username

    if message.text.startswith("/start "):
        ref_id = message.text.split()[1]
        if ref_id != user_id:
            add_ref(ref_id, user_id, username)

    if not check_join(message.from_user.id):
        bot.send_message(message.chat.id,
                         f"Lütfen katıl:\n{KANAL_LINK}\n{GRUP_LINK}")
        return

    ref_link = get_ref_link(user_id)
    bot.send_message(message.chat.id,
                     f"Referans linkin:\n{ref_link}")

# ---------------- KOMUTLAR ----------------
@bot.message_handler(commands=["ref"])
def ref_handler(message):
    user_id = str(message.from_user.id)
    count = DATA["refs"].get(user_id, 0)
    bot.send_message(message.chat.id, f"Referansın: {count}")

# ---------------- BOT RUN ----------------
def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print("Hata:", e)
            time.sleep(5)

# ---------------- THREADS ----------------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    threading.Thread(target=run_bot).start()
