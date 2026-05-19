from flask_login import LoginManager, UserMixin, login_user, \
    login_required, logout_user, current_user

from flask import Flask, request, render_template, redirect, send_from_directory

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime

import os
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = "secret-key"

# ------------------------
# ログイン管理
# ------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ------------------------
# フォルダ設定
# ------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ------------------------
# 拡張子制限
# ------------------------
ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "heic", "heif", "webp"
}


def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------------
# DB初期化
# ------------------------
def init_db():
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    # ユーザー
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)

    # 画像情報
    cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            username TEXT,
            filename TEXT,
            upload_time TEXT
        )
    """)

    conn.commit()
    conn.close()


# ------------------------
# Userクラス
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
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cur.fetchone()
    conn.close()

    return user


def insert_user(username, password_hash):
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users VALUES (?, ?)",
        (username, password_hash)
    )

    conn.commit()
    conn.close()


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

    if request.method == "POST":

        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()

        if get_user(username):

            error = "このユーザー名は既に使われています"

        else:

            hashed = generate_password_hash(password)

            insert_user(username, hashed)

            return redirect("/login")

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
# トップページ（画像一覧）
# ------------------------
@app.route("/")
@login_required
def index():

    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT filename, upload_time
        FROM images
        WHERE username=?
        ORDER BY upload_time DESC
    """, (current_user.id,))

    images = cur.fetchall()
    conn.close()

    return render_template("index.html", images=images)


# ------------------------
# アップロード
# ------------------------
@app.route("/upload", methods=["POST"])
@login_required
def upload():

    error = None
    file = request.files["photo"]

    if not file:
        error = "ファイルが選択されていません"

    elif not allowed_file(file.filename):
        error = "対応していないファイル形式です"

    else:

        user_folder = os.path.join(UPLOAD_FOLDER, current_user.id)
        os.makedirs(user_folder, exist_ok=True)

        ext = os.path.splitext(file.filename)[1]
        unique_name = str(uuid.uuid4()) + ext

        filepath = os.path.join(user_folder, unique_name)
        file.save(filepath)

        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        image_id = str(uuid.uuid4())

        conn = sqlite3.connect("app.db")
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO images VALUES (?, ?, ?, ?)
        """, (
            image_id,
            current_user.id,
            unique_name,
            upload_time
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("index.html", error=error)


# ------------------------
# 画像表示
# ------------------------
@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):

    user_folder = os.path.join(UPLOAD_FOLDER, current_user.id)

    return send_from_directory(user_folder, filename)


# ------------------------
# 削除
# ------------------------
@app.route("/delete/<filename>", methods=["POST"])
@login_required
def delete_file(filename):

    user_folder = os.path.join(UPLOAD_FOLDER, current_user.id)
    filepath = os.path.join(user_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)

    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM images
        WHERE filename=? AND username=?
    """, (filename, current_user.id))

    conn.commit()
    conn.close()

    return redirect("/")


# ------------------------
# 起動
# ------------------------
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
