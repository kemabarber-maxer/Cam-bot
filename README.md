# Cam Scan Bot v2 - Kredi Sistemi + Admin Paneli + Link Suresi

## Ozellikler
- /start -> Link verir (5 kredi ile baslar)
- Kredi bitince link vermez
- Linkler 10 DAKIKA gecerli
- Link suresi dolunca "Link Gecersiz" sayfasi
- Admin paneli /admin
- Admin Telegram'dan kredi ekleyebilir
- Her kullaniciya otomatik ID
- Tum fotograflar admin panelinde

## Yeni Ozellik: Link Suresi
- Her link 10 dakika gecerli
- 10 dakika sonra link otomatik silinir
- Hedef tiklayinca "Link Gecersiz veya Suresi Doldu" gorur
- Kullanici mesajinda bitis zamani yazar (ornegin: 14:30'a kadar)

## Dosya Yapisi
```
proje/
├── main.py              <- Bot kodu (Flask + Telegram)
├── admin.py             <- Admin paneli blueprint
├── database.py          <- SQLite veritabani
├── requirements.txt     <- Flask + requests
├── Procfile             <- web: python main.py
├── static/
│   └── capture.html     <- Kamera sayfasi
└── README.md
```

## Railway Environment Variables
```
BOT_TOKEN = 8890650354:AAHG_DYLxeIsZMdTxZneIK7ZzbaOJlGsvyA
ADMIN_TELEGRAM_ID = [ADMININ_TELEGRAM_ID]
ADMIN_PASSWORD = admin123
SECRET_KEY = rastgele-bir-anahtar
```

## Admin Komutlari (Telegram)
```
/addcredit [ID] [MIKTAR]  -> Kullaniciya kredi ekle
/users                    -> Kullanici listesi
/admin                    -> Admin bilgisi
```

## Kullanici Komutlari
```
/start  -> Link al (1 kredi duser, 10 dk gecerli)
/kredi  -> Kredi sorgula
/id     -> ID ogren
```

## Admin Paneli
URL: https://web-production-2428c.up.railway.app/admin
Sifre: ADMIN_PASSWORD degiskeni

## Link Suresi Akisi
1. /start -> Link olusturulur (10 dk gecerli)
2. Kullanici mesajinda bitis zamani gorur
3. Hedef tiklayinca kamera acilir
4. 10 dakika sonra link otomatik kapanir
5. Hedef tekrar tiklayinca "Link Gecersiz" gorur

## Deploy
1. GitHub repo'yu guncelle
2. Railway -> Redeploy
3. Environment Variables ekle
4. Webhook set et
