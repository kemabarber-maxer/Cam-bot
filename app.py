import os
import base64
import asyncio
import logging
from io import BytesIO
from PIL import Image
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlite3
import uuid
from datetime import datetime

# ==================== AYARLAR ====================
TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL", "")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    raise ValueError("BOT_TOKEN çevre değişkeni ayarlanmamış!")

# ==================== VERİTABANI ====================
DB_FILE = "/tmp/tokens.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER,
        username TEXT,
        created_at TIMESTAMP,
        used BOOLEAN DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def create_token(user_id, username):
    token = str(uuid.uuid4()).replace("-", "")[:16]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tokens (token, user_id, username, created_at) VALUES (?, ?, ?, ?)",
              (token, user_id, username, datetime.now()))
    conn.commit()
    conn.close()
    return token

def get_user_by_token(token):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, username, used FROM tokens WHERE token = ?", (token,))
    result = c.fetchone()
    conn.close()
    return result

def mark_used(token):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tokens SET used = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()

init_db()

# ==================== HTML TEMPLATE ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📷 Kamera</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 500px;
            text-align: center;
        }
        h1 { font-size: 24px; margin-bottom: 10px; }
        .subtitle { color: #a0a0a0; margin-bottom: 20px; font-size: 14px; }
        .video-container {
            position: relative;
            width: 100%;
            aspect-ratio: 3/4;
            background: #0f0f1a;
            border-radius: 20px;
            overflow: hidden;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        video, canvas {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        canvas { display: none; }
        .btn {
            width: 100%;
            padding: 18px;
            border: none;
            border-radius: 15px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 12px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:active { transform: scale(0.95); }
        .btn-success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            display: none;
        }
        .btn-danger {
            background: #e94560;
            color: white;
        }
        .status {
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
            font-size: 14px;
            display: none;
        }
        .status.success { background: rgba(17, 153, 142, 0.2); color: #38ef7d; }
        .status.error { background: rgba(233, 69, 96, 0.2); color: #e94560; }
        .status.info { background: rgba(102, 126, 234, 0.2); color: #667eea; }
        #start-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
        }
        .permission-icon { font-size: 60px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📷 Kamera Paylaşım</h1>
        <p class="subtitle">Merhaba {{ username }}! Fotoğraf çekmek için kameranızı açın</p>
        
        <div class="video-container">
            <div id="start-screen">
                <div class="permission-icon">📸</div>
                <p>Kamera izni gerekiyor</p>
            </div>
            <video id="video" autoplay playsinline></video>
            <canvas id="canvas"></canvas>
        </div>
        
        <button class="btn btn-primary" id="btn-start" onclick="startCamera()">🎥 Kamerayı Aç</button>
        <button class="btn btn-success" id="btn-snap" onclick="takePhoto()">📸 Fotoğraf Çek & Gönder</button>
        <button class="btn btn-danger" id="btn-stop" onclick="stopCamera()" style="display:none;">⏹️ Kamerayı Kapat</button>
        
        <div class="status" id="status"></div>
    </div>

    <script>
        const token = "{{ token }}";
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const startScreen = document.getElementById('start-screen');
        const btnStart = document.getElementById('btn-start');
        const btnSnap = document.getElementById('btn-snap');
        const btnStop = document.getElementById('btn-stop');
        const status = document.getElementById('status');
        let stream = null;

        function showStatus(msg, type) {
            status.textContent = msg;
            status.className = `status ${type}`;
            status.style.display = 'block';
        }

        async function startCamera() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
                    audio: false 
                });
                
                video.srcObject = stream;
                startScreen.style.display = 'none';
                btnStart.style.display = 'none';
                btnSnap.style.display = 'block';
                btnStop.style.display = 'block';
                
                showStatus('✅ Kamera aktif! Fotoğraf çekmek için yeşil butona basın', 'info');
                
            } catch (err) {
                showStatus('❌ Kamera erişimi reddedildi: ' + err.message, 'error');
            }
        }

        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            video.srcObject = null;
            startScreen.style.display = 'flex';
            btnStart.style.display = 'block';
            btnSnap.style.display = 'none';
            btnStop.style.display = 'none';
            showStatus('⏹️ Kamera kapatıldı', 'info');
        }

        async function takePhoto() {
            if (!stream) return;
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(video, 0, 0);
            
            const imageData = canvas.toDataURL('image/jpeg', 0.9);
            
            btnSnap.disabled = true;
            btnSnap.textContent = '📤 Gönderiliyor...';
            
            try {
                const response = await fetch('/upload-photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: token, image: imageData })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('✅ Fotoğraf başarıyla Telegram botunuza gönderildi!', 'success');
                    btnSnap.textContent = '✅ Gönderildi';
                    setTimeout(() => {
                        btnSnap.textContent = '📸 Fotoğraf Çek & Gönder';
                        btnSnap.disabled = false;
                    }, 3000);
                } else {
                    throw new Error(result.error);
                }
                
            } catch (err) {
                showStatus('❌ Gönderim hatası: ' + err.message, 'error');
                btnSnap.disabled = false;
                btnSnap.textContent = '📸 Fotoğraf Çek & Gönder';
            }
        }

        window.addEventListener('beforeunload', () => {
            if (stream) stream.getTracks().forEach(track => track.stop());
        });
    </script>
</body>
</html>
'''

# ==================== FLASK APP ====================
app = Flask(__name__)
CORS(app)
bot = Bot(token=TOKEN)

@app.route("/")
def home():
    return "✅ Cam Bot çalışıyor! Bot üzerinden /start yazın."

@app.route("/camera")
def camera_page():
    token = request.args.get("token")
    if not token:
        return "❌ Geçersiz link", 400
    
    user = get_user_by_token(token)
    if not user:
        return "❌ Link geçersiz veya süresi dolmuş", 400
    
    user_id, username, used = user
    return render_template_string(HTML_TEMPLATE, token=token, username=username)

@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    data = request.get_json()
    token = data.get("token")
    image_data = data.get("image")
    
    if not token or not image_data:
        return jsonify({"success": False, "error": "Eksik veri"}), 400
    
    user = get_user_by_token(token)
    if not user:
        return jsonify({"success": False, "error": "Geçersiz token"}), 400
    
    user_id, username, used = user
    
    try:
        image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        temp_path = f"/tmp/photo_{token}.jpg"
        image.save(temp_path, "JPEG")
        
        async def send():
            await bot.send_photo(
                chat_id=user_id,
                photo=open(temp_path, 'rb'),
                caption=f"📸 {username} adlı kullanıcıdan yeni fotoğraf!"
            )
        
        asyncio.run(send())
        
        os.remove(temp_path)
        mark_used(token)
        
        return jsonify({"success": True, "message": "Fotoğraf gönderildi!"})
        
    except Exception as e:
        logging.error(f"Upload hatası: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== TELEGRAM BOT ====================
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    token = create_token(user_id, username)
    link = f"{BASE_URL}/camera?token={token}"
    
    keyboard = [[InlineKeyboardButton("📷 Kamerayı Aç", url=link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Merhaba {username}!\n\n"
        f"📸 Kamera erişimi için linke tıklayın:\n\n"
        f"`{link}`\n\n"
        f"⚠️ Kamera izni sizden istenecek. "
        f"Fotoğraf çek butonuna basmadan görüntü alınmaz.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

application.add_handler(CommandHandler("start", start))

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        await application.process_update(update)
        return "OK", 200
    except Exception as e:
        logging.error(f"Webhook hatası: {e}")
        return "Error", 500

@app.before_request
def init():
    if not getattr(app, '_webhook_set', False) and BASE_URL:
        webhook_url = f"{BASE_URL}/webhook"
        asyncio.run(bot.set_webhook(url=webhook_url))
        app._webhook_set = True
        print(f"✅ Webhook ayarlandı: {webhook_url}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
