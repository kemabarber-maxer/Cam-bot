
# Railway için main.py (bot.py'yi import eder - Railway main.py arıyor)
main_code = '''from bot import app, bot_app, TOKEN, WEBHOOK_URL
import os
import asyncio

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
'''

with open("/mnt/agents/output/main.py", "w") as f:
    f.write(main_code)

# Railway için Procfile (opsiyonel ama önerilir)
procfile = '''web: gunicorn main:app
'''

with open("/mnt/agents/output/Procfile", "w") as f:
    f.write(procfile)

print("✅ main.py yazıldı (Railway için)")
print("✅ Procfile yazıldı")
