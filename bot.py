import os
import json
from datetime import date, timedelta
import telebot
from flask import Flask
from threading import Thread
import threading
import requests
import time

# ---------------------
# BOT & ENVIRONMENT
# ---------------------
TOKEN = os.environ.get("BOT_TOKEN")  # Render Environment Variable
KANAL_LINK = "@bedavakampanyalarorg"
GRUP_LINK = "vipgrubum"
DAILY_ODUL = 2  # GB

bot = telebot.TeleBot(TOKEN)

# ---------------------
# REFERANS VERİSİ
# ---------------------
def load_refs():
    try:
        with open("ref.json","r") as f:
            return json.load(f)
    except:
        return {"refs":{},"users":{},"daily_refs":{}}

def save_refs():
    with open("ref.json","w") as f:
        json.dump(REFERANS_DATABASE,f)

REFERANS_DATABASE = load_refs()

def add_ref(ref_id, username=None):
    uid = str(ref_id)
    # Toplam referans
    REFERANS_DATABASE["refs"][uid] = REFERANS_DATABASE["refs"].get(uid,0)+1

    # Günlük referans
    today_str = date.today().isoformat()
    if "daily_refs" not in REFERANS_DATABASE:
        REFERANS_DATABASE["daily_refs"] = {}
    if today_str not in REFERANS_DATABASE["daily_refs"]:
        REFERANS_DATABASE["daily_refs"][today_str] = {}
    REFERANS_DATABASE["daily_refs"][today_str][uid] = REFERANS_DATABASE["daily_refs"][today_str].get(uid,0)+1

    # Username kaydı
    if username:
        REFERANS_DATABASE["users"][uid] = username

    # Son 4 günü sakla
    dates_sorted = sorted(REFERANS_DATABASE["daily_refs"].keys())
    if len(dates_sorted) > 4:
        oldest = dates_sorted[0]
        del REFERANS_DATABASE["daily_refs"][oldest]

    save_refs()

def check_reward(user_id):
    uid = str(user_id)
    return REFERANS_DATABASE["refs"].get(uid,0) >= 25

# ---------------------
# ZORUNLU KANAL & GRUP
# ---------------------
def kanalda_ve_grupta_mi(user_id):
    try:
        uye = bot.get_chat_member(KANAL_LINK,user_id)
        kanal = uye.status in ["member","administrator","creator"]
    except:
        kanal = False
    try:
        uye2 = bot.get_chat_member(GRUP_LINK,user_id)
        grup = uye2.status in ["member","administrator","creator"]
    except:
        grup = False
    return kanal and grup

# ---------------------
# START KOMUTU
# ---------------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    ref = message.text.split()[1] if len(message.text.split())>1 else None

    if ref:
        try:
            ref = int(ref)
            if ref != user_id:
                add_ref(ref, username)
        except:
            pass

    if not kanalda_ve_grupta_mi(user_id):
        bot.send_message(message.chat.id,
            f"🚨 Botu kullanmak için kanala ve gruba katıl:\n"
            f"{KANAL_LINK}\nhttps://t.me/{GRUP_LINK}"
        )
        return

    refs = REFERANS_DATABASE["refs"].get(str(user_id),0)
    bot.send_message(message.chat.id,
        f"✅ SHELBY BOT AKTİF\nReferans: {refs}\nBot işte referans linkin: {KANAL_LINK}\n\n"
        f"Komutlar:\n/durum\n/top\n/top4gun\n/odul"
    )

# ---------------------
# DURUM KOMUTU
# ---------------------
@bot.message_handler(commands=["durum"])
def durum(message):
    user_id = message.from_user.id
    refs = REFERANS_DATABASE["refs"].get(str(user_id),0)
    kalan = max(25-refs,0)
    odul = "✅ Ödül kazanıldı" if check_reward(user_id) else "❌ Ödül henüz kazanılmadı"
    bot.send_message(message.chat.id,
        f"📊 PANEL\nReferanslarınız: {refs} / 25\nKalan: {kalan}\n"
        f"Referans linkiniz: {KANAL_LINK}\nÖdül durumu: {odul}"
    )

# ---------------------
# TOP KOMUTU (en çok referans)
# ---------------------
@bot.message_handler(commands=["top"])
def top_list(message):
    sorted_refs = sorted(REFERANS_DATABASE["refs"].items(), key=lambda x: x[1], reverse=True)
    text = "🏆 En çok referans yapanlar:\n"
    for i,(uid,count) in enumerate(sorted_refs[:10],1):
        username = REFERANS_DATABASE["users"].get(uid,"Bilinmiyor")
        text += f"{i}. {username} ➜ {count} referans\n"
    bot.send_message(message.chat.id,text)

# ---------------------
# TOP 4 GÜN KOMUTU
# ---------------------
@bot.message_handler(commands=["top4gun"])
def top_4gun(message):
    today = date.today()
    daily_refs = REFERANS_DATABASE.get("daily_refs",{})
    last_4_days = [(today - timedelta(days=i)).isoformat() for i in range(4)]
    total_refs = {}
    for day in last_4_days:
        day_data = daily_refs.get(day,{})
        for uid,count in day_data.items():
            total_refs[uid] = total_refs.get(uid,0)+count
    sorted_refs = sorted(total_refs.items(), key=lambda x:x[1], reverse=True)
    text = "📊 Son 4 günün en çok referans yapanları:\n"
    for i,(uid,count) in enumerate(sorted_refs[:10],1):
        username = REFERANS_DATABASE["users"].get(uid,"Bilinmiyor")
        text += f"{i}. {username} ➜ {count} referans\n"
    bot.send_message(message.chat.id,text)

# ---------------------
# ÖDÜL KOMUTU
# ---------------------
@bot.message_handler(commands=["odul"])
def odul(message):
    user_id = message.from_user.id
    if check_reward(user_id):
        bot.send_message(message.chat.id,"🎉 25 referans topladınız! 2GB ödül kazandınız.")
    else:
        bot.send_message(message.chat.id,f"🔹 Şu an {REFERANS_DATABASE['refs'].get(str(user_id),0)} referansınız var. 25 referansa ulaşınca ödül kazanacaksınız.")

# ---------------------
# GÜNLÜK ÖDÜL (manuel veya cron ile çalıştır)
# ---------------------
def daily_reward():
    today = date.today()
    daily_refs = REFERANS_DATABASE.get("daily_refs",{})
    total_refs = {}
    for day_data in daily_refs.values():
        for uid,count in day_data.items():
            total_refs[uid] = total_refs.get(uid,0)+count
    sorted_refs = sorted(total_refs.items(), key=lambda x:x[1], reverse=True)
    if sorted_refs:
        winner_id = sorted_refs[0][0]
        try:
            bot.send_message(winner_id,f"🎉 Günün en çok referans toplayanı sensin! {DAILY_ODUL}GB ödül hazır!")
        except Exception as e:
            print("Ödül mesajı gönderilemedi:", e)

# ---------------------
# FLASK SERVER (Render Web Service)
# ---------------------
app = Flask('')
@app.route('/')
def home():
    return "SHELBY BOT AKTİF"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",3000)))

Thread(target=run_flask).start()

# ---------------------
# BOTU 7/24 UYANDIRMA (SELF-PING)
# ---------------------
def keep_alive():
    while True:
        try:
            url = f"https://{os.environ.get('RENDER_SERVICE_NAME')}.onrender.com/"
            requests.get(url, timeout=5)
        except:
            pass
        time.sleep(300)  # 5 dakikada bir ping

threading.Thread(target=keep_alive).start()

# ---------------------
# TELEBOT 7/24
# ---------------------
bot.infinity_polling()
