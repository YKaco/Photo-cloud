from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, request, render_template, redirect, abort, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

import cloudinary
import cloudinary.uploader
import cloudinary.api

import os
import sqlite3
import uuid

load_dotenv()

# ------------------------
# アプリ設定
# ------------------------
app = Flask(__name__)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY 環境変数が設定されていません")
app.secret_key = secret_key

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

# ------------------------
# Cloudinary設定
# ------------------------
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# ------------------------
# ログイン管理
# ------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "heic", "heif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------
# DB初期化
# ------------------------
def init_db():
    with sqlite3.connect("app.db") as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT
            )
        """)
        # cloudinary_id: 削除に使うpublic_id、image_url: 表示用URL
        cur.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                username TEXT,
                cloudinary_id TEXT,
                image_url TEXT,
                upload_time TEXT
            )
        """)
        conn.commit()

# ------------------------
# User
# ------------------------
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ------------------------
# DB操作
# ------------------------
def get_user(username):
    with sqlite3.connect("app.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        return cur.fetchone()

def insert_user(username, password_hash):
    with sqlite3.connect("app.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (?, ?)", (username, password_hash))
        conn.commit()

# ------------------------
# ログイン
# ------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()
        user = get_user(username)
        if user and check_password_hash(user[1], password):
            login_user(User(username))
            return redirect("/")
        else:
            error = "IDまたはパスワードが違います"
    return render_template("login.html", error=error)

# ------------------------
# 新規登録
# ------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.cookies.get("registered"):
        return render_template("register.html", error="この端末では登録済みです")
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()
        password_confirm = request.form.get("password_confirm", "").strip()
        if password != password_confirm:
            error = "パスワードが一致しません"
        elif get_user(username):
            error = "このユーザー名は既に使われています"
        else:
            insert_user(username, generate_password_hash(password))
            response = app.make_response(redirect("/login"))
            response.set_cookie("registered", "1", max_age=60 * 60 * 24 * 365)
            return response
    return render_template("register.html", error=error)

# ------------------------
# ログアウト
# ------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ------------------------
# パスワード変更
# ------------------------
@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    error = None
    success = None
    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        new_password_confirm = request.form.get("new_password_confirm", "").strip()
        user = get_user(current_user.id)
        if not user or not check_password_hash(user[1], current_password):
            error = "現在のパスワードが正しくありません"
        elif new_password != new_password_confirm:
            error = "新しいパスワードが一致しません"
        elif len(new_password) < 4:
            error = "パスワードは4文字以上で設定してください"
        else:
            with sqlite3.connect("app.db") as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET password=? WHERE username=?",
                    (generate_password_hash(new_password), current_user.id)
                )
                conn.commit()
            success = "パスワードを変更しました"
    return render_template("change_password.html", error=error, success=success)

# ------------------------
# トップページ
# ------------------------
@app.route("/")
@login_required
def index():
    view = request.args.get("view", "month")
    sort = request.args.get("sort", "desc")
    order = "DESC" if sort != "asc" else "ASC"

    with sqlite3.connect("app.db") as conn:
        cur = conn.cursor()

        if view == "list":
            cur.execute(f"""
                SELECT cloudinary_id, image_url, upload_time
                FROM images
                WHERE username=?
                ORDER BY upload_time {order}
            """, (current_user.id,))
            images = cur.fetchall()
            return render_template("index.html", images=images, view="list", sort=sort)

        cur.execute(f"""
            SELECT cloudinary_id, image_url, upload_time,
                   strftime('%Y-%m', upload_time)
            FROM images
            WHERE username=?
            ORDER BY upload_time {order}
        """, (current_user.id,))
        rows = cur.fetchall()

    grouped = defaultdict(list)
    for cloudinary_id, image_url, time, month in rows:
        grouped[month].append((cloudinary_id, image_url, time))

    return render_template("index.html", images=grouped, view="month", sort=sort)

# ------------------------
# アップロード
# ------------------------
@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("photo")
    if not file or file.filename == "":
        return redirect("/")
    if not allowed_file(file.filename):
        return redirect("/")

    # Cloudinaryにアップロード（ユーザーごとのフォルダに保存）
    result = cloudinary.uploader.upload(
        file,
        folder=f"photo_cloud/{current_user.id}",
        resource_type="image"
    )

    cloudinary_id = result["public_id"]
    image_url = result["secure_url"]
    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect("app.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO images VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), current_user.id, cloudinary_id, image_url, upload_time)
        )
        conn.commit()

    return redirect("/")

# ------------------------
# 削除
# ------------------------
@app.route("/delete/<path:cloudinary_id>", methods=["POST"])
@login_required
def delete_file(cloudinary_id):
    # 所有者確認
    with sqlite3.connect("app.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM images WHERE cloudinary_id=? AND username=?",
            (cloudinary_id, current_user.id)
        )
        if not cur.fetchone():
            abort(403)

        # Cloudinaryから削除
        cloudinary.uploader.destroy(cloudinary_id)

        # DBから削除
        cur.execute(
            "DELETE FROM images WHERE cloudinary_id=? AND username=?",
            (cloudinary_id, current_user.id)
        )
        conn.commit()

    return redirect("/")

# ------------------------
# 起動
# ------------------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
