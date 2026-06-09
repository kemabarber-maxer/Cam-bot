from bot import app, bot_app, TOKEN, WEBHOOK_URL
import os
import asyncio

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
