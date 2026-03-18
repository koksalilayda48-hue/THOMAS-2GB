import os
import json
from datetime import date, timedelta
import telebot
import time

TOKEN = os.environ.get("BOT_TOKEN")

KANAL = "@bedavakampanyalarorg"
GRUP = "vipgrubum"

bot = telebot.TeleBot(TOKEN)

# ---------------- DATA ----------------
def load():
    try:
        with open("ref.json","r") as f:
            return json.load(f)
    except:
        return {"refs":{},"users":{},"daily":{},"joined":[]}

def save():
    with open("ref.json","w") as f:
        json.dump(DB,f)

DB = load()

# ---------------- REFERANS ----------------
def add_ref(ref_id, new_user, username=None):
    ref_id = str(ref_id)
    new_user = str(new_user)

    if new_user in DB["joined"]:
        return

    DB["joined"].append(new_user)

    DB["refs"][ref_id] = DB["refs"].get(ref_id,0)+1

    today = date.today().isoformat()
    if today not in DB["daily"]:
        DB["daily"][today] = {}

    DB["daily"][today][ref_id] = DB["daily"][today].get(ref_id,0)+1

    if username:
        DB["users"][ref_id] = username

    # sadece son 4 gün
    keys = sorted(DB["daily"].keys())
    if len(keys) > 4:
        del DB["daily"][keys[0]]

    save()

# ---------------- KONTROL ----------------
def check(user_id):
    try:
        k = bot.get_chat_member(KANAL,user_id)
        g = bot.get_chat_member(GRUP,user_id)
        return k.status in ["member","creator","administrator"] and g.status in ["member","creator","administrator"]
    except:
        return False

def ref_link(user_id):
    return f"https://t.me/{bot.get_me().username}?start={user_id}"

# ---------------- START ----------------
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    username = m.from_user.username

    args = m.text.split()

    if len(args) > 1:
        try:
            ref = int(args[1])
            if ref != uid:
                add_ref(ref, uid, username)
        except:
            pass

    if not check(uid):
        bot.send_message(m.chat.id,
            f"🚨 Katılman lazım:\n{KANAL}\nhttps://t.me/{GRUP}"
        )
        return

    refs = DB["refs"].get(str(uid),0)

    bot.send_message(m.chat.id,
        f"🔥 SHELBY BOT\n\n"
        f"📊 Referansın: {refs}\n\n"
        f"🔗 Linkin:\n{ref_link(uid)}\n\n"
        f"/durum\n/top\n/top4gun\n/odul"
    )

# ---------------- DURUM ----------------
@bot.message_handler(commands=["durum"])
def durum(m):
    uid = m.from_user.id
    refs = DB["refs"].get(str(uid),0)
    kalan = max(25-refs,0)

    bot.send_message(m.chat.id,
        f"📊 PANEL\n\n"
        f"{refs}/25 referans\n"
        f"Kalan: {kalan}\n\n"
        f"🔗 {ref_link(uid)}"
    )

# ---------------- TOP ----------------
@bot.message_handler(commands=["top"])
def top(m):
    s = sorted(DB["refs"].items(), key=lambda x:x[1], reverse=True)

    txt = "🏆 EN İYİLER\n\n"
    for i,(uid,count) in enumerate(s[:10],1):
        name = DB["users"].get(uid,"User")
        txt += f"{i}. {name} ➜ {count}\n"

    bot.send_message(m.chat.id,txt)

# ---------------- TOP 4 GÜN ----------------
@bot.message_handler(commands=["top4gun"])
def top4(m):
    today = date.today()
    total = {}

    for i in range(4):
        d = (today - timedelta(days=i)).isoformat()
        data = DB["daily"].get(d,{})
        for uid,count in data.items():
            total[uid] = total.get(uid,0)+count

    s = sorted(total.items(), key=lambda x:x[1], reverse=True)

    txt = "📊 SON 4 GÜN\n\n"
    for i,(uid,count) in enumerate(s[:10],1):
        name = DB["users"].get(uid,"User")
        txt += f"{i}. {name} ➜ {count}\n"

    bot.send_message(m.chat.id,txt)

# ---------------- ÖDÜL ----------------
@bot.message_handler(commands=["odul"])
def odul(m):
    uid = m.from_user.id
    refs = DB["refs"].get(str(uid),0)

    if refs >= 25:
        bot.send_message(m.chat.id,"🎉 2GB KAZANDIN!")
    else:
        bot.send_message(m.chat.id,f"{refs}/25 referans")

# ---------------- 7/24 ÇALIŞMA ----------------
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Hata:", e)
        time.sleep(5)
