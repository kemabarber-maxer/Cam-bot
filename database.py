import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DB_PATH", "cam_bot.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            credits INTEGER DEFAULT 5,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT,
            photo_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            target_id INTEGER,
            action TEXT,
            amount INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def get_or_create_user(telegram_id, username):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (telegram_id, username, credits) VALUES (?, ?, 5)",
                  (telegram_id, username))
        conn.commit()
        c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = c.fetchone()
    conn.close()
    return dict(user)

def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_telegram_id(telegram_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def add_credits(user_id, amount):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def deduct_credit(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    if row and row["credits"] > 0:
        c.execute("UPDATE users SET credits = credits - 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def create_link(user_id, token, minutes=10):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now()
    expires = now + timedelta(minutes=minutes)
    c.execute("INSERT INTO links (user_id, token, expires_at) VALUES (?, ?, ?)",
              (user_id, token, expires.isoformat()))
    conn.commit()
    conn.close()

def is_link_valid(token):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM links WHERE token = ? AND used = 0", (token,))
    link = c.fetchone()
    conn.close()
    if not link:
        return False
    expires = datetime.fromisoformat(link["expires_at"])
    if datetime.now() > expires:
        return False
    return True

def mark_link_used(token):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE links SET used = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def save_photo(user_id, token, photo_data):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO photos (user_id, token, photo_data) VALUES (?, ?, ?)",
              (user_id, token, photo_data))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return users

def get_all_photos():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT p.*, u.username, u.telegram_id FROM photos p JOIN users u ON p.user_id = u.id ORDER BY p.id DESC")
    photos = [dict(row) for row in c.fetchall()]
    conn.close()
    return photos

def log_admin_action(admin_id, target_id, action, amount):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO admin_logs (admin_id, target_id, action, amount) VALUES (?, ?, ?, ?)",
              (admin_id, target_id, action, amount))
    conn.commit()
    conn.close()

def get_admin_logs():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM admin_logs ORDER BY id DESC LIMIT 100")
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    return logs
