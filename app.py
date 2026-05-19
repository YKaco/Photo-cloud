<<<<<<< HEAD
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, request, render_template, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import defaultdict
=======
from flask_login import LoginManager, UserMixin, login_user, \
    login_required, logout_user, current_user

from flask import Flask, request, render_template, redirect, send_from_directory

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8

import os
import sqlite3
import uuid

<<<<<<< HEAD
# ------------------------
# アプリ設定
# ------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
=======
app = Flask(__name__)
app.secret_key = "secret-key"
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8

# ------------------------
# ログイン管理
# ------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

<<<<<<< HEAD
# ------------------------
# アップロード設定
# ------------------------
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "heic", "heif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
=======

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

>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8

# ------------------------
# DB初期化
# ------------------------
def init_db():
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

<<<<<<< HEAD
=======
    # ユーザー
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)

<<<<<<< HEAD
=======
    # 画像情報
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
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

<<<<<<< HEAD
# ------------------------
# User
=======

# ------------------------
# Userクラス
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
# ------------------------
class User(UserMixin):
    def __init__(self, id):
        self.id = id

<<<<<<< HEAD
=======

>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

<<<<<<< HEAD
=======

>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
# ------------------------
# DB操作
# ------------------------
def get_user(username):
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
<<<<<<< HEAD
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def insert_user(username, password_hash):
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO users VALUES (?, ?)", (username, password_hash))
    conn.commit()
    conn.close()

=======

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


>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
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
<<<<<<< HEAD
            login_user(User(username))
            return redirect("/")
=======

            login_user(User(username))

            return redirect("/")

>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
        else:
            error = "IDまたはパスワードが違います"

    return render_template("login.html", error=error)

<<<<<<< HEAD
# ------------------------
# 新規登録（1端末制限）
=======

# ------------------------
# 新規登録
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
# ------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

<<<<<<< HEAD
    if request.cookies.get("registered"):
        return render_template("register.html", error="この端末では登録済みです")

=======
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
    if request.method == "POST":

        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()

        if get_user(username):
<<<<<<< HEAD
            error = "このユーザー名は既に使われています"

        else:
            hashed = generate_password_hash(password)
            insert_user(username, hashed)

            response = redirect("/login")
            response = app.make_response(response)

            response.set_cookie(
                "registered",
                "1",
                max_age=60 * 60 * 24 * 365
            )

            return response

    return render_template("register.html", error=error)

=======

            error = "このユーザー名は既に使われています"

        else:

            hashed = generate_password_hash(password)

            insert_user(username, hashed)

            return redirect("/login")

    return render_template("register.html", error=error)


>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
# ------------------------
# ログアウト
# ------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

<<<<<<< HEAD
# ------------------------
# トップページ（安定版）
=======

# ------------------------
# トップページ（画像一覧）
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
# ------------------------
@app.route("/")
@login_required
def index():

<<<<<<< HEAD
    view = request.args.get("view", "month")

    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    # list用（2列）
    if view == "list":

        cur.execute("""
            SELECT filename, upload_time
            FROM images
            WHERE username=?
            ORDER BY upload_time DESC
        """, (current_user.id,))

        images = cur.fetchall()
        conn.close()

        return render_template(
            "index.html",
            images=images,
            view="list"
        )

    # month用（3列）
    cur.execute("""
        SELECT filename, upload_time,
               strftime('%Y-%m', upload_time)
=======
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT filename, upload_time
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
        FROM images
        WHERE username=?
        ORDER BY upload_time DESC
    """, (current_user.id,))

<<<<<<< HEAD
    rows = cur.fetchall()
    conn.close()

    grouped = defaultdict(list)

    for filename, time, month in rows:
        grouped[month].append((filename, time))

    return render_template(
        "index.html",
        images=grouped,
        view="month"
    )
=======
    images = cur.fetchall()
    conn.close()

    return render_template("index.html", images=images)

>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8

# ------------------------
# アップロード
# ------------------------
@app.route("/upload", methods=["POST"])
@login_required
def upload():

<<<<<<< HEAD
    file = request.files.get("photo")

    if not file or file.filename == "":
        return redirect("/")

    if not allowed_file(file.filename):
        return redirect("/")

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1]

    unique_name = str(uuid.uuid4()) + ext

    user_folder = os.path.join(UPLOAD_FOLDER, current_user.id)
    os.makedirs(user_folder, exist_ok=True)

    file.save(os.path.join(user_folder, unique_name))

    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO images VALUES (?, ?, ?, ?)
    """, (str(uuid.uuid4()), current_user.id, unique_name, upload_time))

    conn.commit()
    conn.close()

    return redirect("/")
=======
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

>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8

# ------------------------
# 画像表示
# ------------------------
@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
<<<<<<< HEAD
    user_folder = os.path.join(UPLOAD_FOLDER, current_user.id)
    return send_from_directory(user_folder, filename)

=======

    user_folder = os.path.join(UPLOAD_FOLDER, current_user.id)

    return send_from_directory(user_folder, filename)


>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
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

<<<<<<< HEAD
=======

>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
# ------------------------
# 起動
# ------------------------
if __name__ == "__main__":
<<<<<<< HEAD

    init_db()
=======
    import os
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
<<<<<<< HEAD
        port=port,
        debug=True
=======
        port=port
>>>>>>> ffe9fd4fb11e09fb55b06fab1edfda8aaf381bb8
    )
