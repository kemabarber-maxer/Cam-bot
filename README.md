
# Güncel README
readme = '''# 📸 Cam Scan Bot - Railway Deploy

## Hata Çözümü: "No module named 'main'"
Railway `main.py` dosyası arıyor. Bu yüzden 2 Python dosyası var:
- `main.py` → Railway giriş noktası (app'i başlatır)
- `bot.py` → Bot mantığı (Flask + Telegram)

## Dosya Yapısı
```
📂 proje/
├── 🐍 main.py              ← Railway giriş noktası
├── 🐍 bot.py               ← Bot mantığı
├── 📄 requirements.txt     ← Python bağımlılıkları
├── 📄 Procfile             ← Railway start komutu
├── 📂 static/
│   └── 📷 capture.html     ← Kamera sayfası
└── 📖 README.md
```

## Railway Environment Variables
```
BOT_TOKEN = 8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY
```
Railway otomatik verir:
- `RAILWAY_PUBLIC_DOMAIN` → senin-app.up.railway.app
- `PORT` → dinamik port

## Deploy Adımları
1. GitHub repo oluştur, tüm dosyaları push et
2. Railway → New Project → Deploy from GitHub
3. Variables → BOT_TOKEN ekle
4. Deploy otomatik başlar
5. Webhook set et:
```
https://api.telegram.org/bot8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY/setWebhook?url=https://SENIN-APP.up.railway.app/8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY
```
'''

with open("/mnt/agents/output/README.md", "w") as f:
    f.write(readme)

print("✅ README.md güncellendi")
