import os
import json
from datetime import date, timedelta
import telebot
from flask import Flask
from threading import Thread
import threading
import requests
import time

TOKEN = os.environ.get("BOT_TOKEN")

KANAL_LINK = "@bedavakampanyalarorg"
GRUP_LINK = "vipgrubum"
DAILY_ODUL = 2

bot = telebot.TeleBot(TOKEN)

# ---------------- DATA ----------------
def load_data():
    try:
        with open("ref.json","r") as f:
            return json.load(f)
    except:
        return {"refs":{},"users":{},"daily_refs":{},"joined":[]}

def save_data():
    with open("ref.json","w") as f:
        json.dump(DATA,f)

DATA = load_data()

# ---------------- REFERANS EKLE ----------------
def add_ref(ref_id, new_user_id, username=None):
    ref_id = str(ref_id)
    new_user_id = str(new_user_id)

    # aynı kişi tekrar sayılmaz
    if new_user_id in DATA["joined"]:
        return

    DATA["joined"].append(new_user_id)

    # toplam referans
    DATA["refs"][ref_id] = DATA["refs"].get(ref_id,0)+1

    # günlük referans
    today = date.today().isoformat()
    if today not in DATA["daily_refs"]:
        DATA["daily_refs"][today] = {}

    DATA["daily_refs"][today][ref_id] = DATA["daily_refs"][today].get(ref_id,0)+1

    # username
    if username:
        DATA["users"][ref_id] = username

    # sadece 4 gün sakla
    keys = sorted(DATA["daily_refs"].keys())
    if len(keys) > 4:
        del DATA["daily_refs"][keys[0]]

    save_data()

# ---------------- KONTROLLER ----------------
def check_join(user_id):
    try:
        k = bot.get_chat_member(KANAL_LINK,user_id)
        g = bot.get_chat_member(GRUP_LINK,user_id)
        return k.status in ["member","creator","administrator"] and g.status in ["member","creator","administrator"]
    except:
        return False

def get_ref_link(user_id):
    return f"https://t.me/{bot.get_me().username}?start={user_id}"

# ---------------- START ----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username

    args = message.text.split()
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id != user_id:
                add_ref(ref_id, user_id, username)
        except:
            pass

    if not check_join(user_id):
        bot.send_message(message.chat.id,
            f"🚨 Katılman gerekiyor:\n{KANAL_LINK}\nhttps://t.me/{GRUP_LINK}"
        )
        return

    refs = DATA["refs"].get(str(user_id),0)
    link = get_ref_link(user_id)

    bot.send_message(message.chat.id,
        f"✅ SHELBY BOT\n\n"
        f"📊 Referans: {refs}\n\n"
        f"🔗 Linkin:\n{link}\n\n"
        f"Komutlar:\n/durum\n/top\n/top4gun\n/odul"
    )

# ---------------- DURUM ----------------
@bot.message_handler(commands=["durum"])
def durum(message):
    user_id = message.from_user.id
    refs = DATA["refs"].get(str(user_id),0)
    kalan = max(25-refs,0)
    link = get_ref_link(user_id)

    bot.send_message(message.chat.id,
        f"📊 PANEL\n\n"
        f"Referans: {refs}/25\n"
        f"Kalan: {kalan}\n\n"
        f"🔗 Linkin:\n{link}"
    )

# ---------------- TOP ----------------
@bot.message_handler(commands=["top"])
def top(message):
    s = sorted(DATA["refs"].items(), key=lambda x:x[1], reverse=True)
    text = "🏆 EN İYİLER\n\n"
    for i,(uid,count) in enumerate(s[:10],1):
        name = DATA["users"].get(uid,"User")
        text += f"{i}. {name} ➜ {count}\n"
    bot.send_message(message.chat.id,text)

# ---------------- TOP 4 GÜN ----------------
@bot.message_handler(commands=["top4gun"])
def top4(message):
    today = date.today()
    total = {}

    for i in range(4):
        day = (today - timedelta(days=i)).isoformat()
        day_data = DATA["daily_refs"].get(day,{})
        for uid,count in day_data.items():
            total[uid] = total.get(uid,0)+count

    s = sorted(total.items(), key=lambda x:x[1], reverse=True)

    text = "📊 SON 4 GÜN\n\n"
    for i,(uid,count) in enumerate(s[:10],1):
        name = DATA["users"].get(uid,"User")
        text += f"{i}. {name} ➜ {count}\n"

    bot.send_message(message.chat.id,text)

# ---------------- ÖDÜL ----------------
@bot.message_handler(commands=["odul"])
def odul(message):
    user_id = message.from_user.id
    refs = DATA["refs"].get(str(user_id),0)

    if refs >= 25:
        bot.send_message(message.chat.id,"🎉 25 REFERANS TAMAMLANDI! 2GB ALDIN")
    else:
        bot.send_message(message.chat.id,f"🔹 {refs}/25 referansın var")

# ---------------- FLASK ----------------
app = Flask('')
@app.route('/')
def home():
    return "BOT AKTİF"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",3000)))

Thread(target=run).start()

# ---------------- SELF PING ----------------
def ping():
    while True:
        try:
            url = f"https://{os.environ.get('RENDER_SERVICE_NAME')}.onrender.com/"
            requests.get(url)
        except:
            pass
        time.sleep(300)

threading.Thread(target=ping).start()

# ---------------- RUN ----------------
bot.infinity_polling()
