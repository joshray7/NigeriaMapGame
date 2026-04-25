from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import json
import os
from sqlalchemy import text

app = Flask(__name__)

# ==========================
# SECRET KEY
# ==========================
app.secret_key = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
)

# ==========================
# DATABASE CONFIG
# ==========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///local.db"

# Fix old Render format
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# IMPORTANT: remove query issues + enforce SSL properly
if "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280
}

# INIT DB
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ==========================
# MODELS
# ==========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    guessed_states = db.Column(db.Text, default="[]")
    high_score = db.Column(db.Integer, default=0)

# ==========================
# ROUTES
# ==========================

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/game")
    return redirect("/login")


# OPTIONAL: initialize DB manually
@app.route("/init-db")
def init_db():
    try:
        with app.app_context():
            db.create_all()
        return "Database created successfully!"
    except Exception as e:
        return f"DB Error: {str(e)}"

@app.route("/debug-db")
def debug_db():
    try:
        db.session.execute(text("SELECT 1"))
        return "DB CONNECTION OK"
    except Exception as e:
        return f"DB ERROR: {str(e)}"

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            return render_template("signup.html", error="User already exists.")

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(username=username, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()

        progress = Progress(user_id=user.id, guessed_states="[]")
        db.session.add(progress)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.verify_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect("/game")

        error = "Invalid username or password."

    return render_template("login.html", error=error)


# ---------- GAME ----------
@app.route("/game")
def game():
    if "user_id" not in session:
        return redirect("/login")

    progress = Progress.query.filter_by(user_id=session["user_id"]).first()

    if not progress:
        progress = Progress(user_id=session["user_id"], guessed_states="[]")
        db.session.add(progress)
        db.session.commit()

    guessed_states = json.loads(progress.guessed_states or "[]")

    return render_template("index.html", guessed_states=guessed_states)


# ---------- SAVE PROGRESS ----------
@app.route("/save_progress", methods=["POST"])
def save_progress():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 403

    data = request.get_json() or {}
    guessed_states = data.get("guessed_states", [])

    progress = Progress.query.filter_by(user_id=session["user_id"]).first()
    if progress:
        progress.guessed_states = json.dumps(guessed_states)
        db.session.commit()

    return jsonify({"status": "ok"})


# ---------- RESET ----------
@app.route("/reset", methods=["POST"])
def reset_game():
    return jsonify(success=True)


# ---------- STATE PAGE ----------
@app.route("/state/<state_name>")
def show_description(state_name):
    return render_template("state.html", state_name=state_name.title())


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app.run()