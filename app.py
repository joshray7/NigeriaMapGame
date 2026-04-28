from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
import json
import os
from sqlalchemy import text

app = Flask(__name__)
load_dotenv()


# ==========================
# SECRET KEY (SAFE)
# ==========================
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set!")
app.config["SECRET_KEY"] = SECRET_KEY

# ==========================
# CSRF PROTECTION
# ==========================
csrf = CSRFProtect(app)
app.config["WTF_CSRF_ENABLED"] = True

# ==========================
# DATABASE CONFIG
# ==========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///local.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ==========================
# INIT EXTENSIONS
# ==========================
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
# SAFE DB INIT
# ==========================
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print("DB INIT ERROR:", e)

# ==========================
# ROUTES
# ==========================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/game")
    return redirect("/login")


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

    try:
        user_id = session["user_id"]

        progress = Progress.query.filter_by(user_id=user_id).first()

        if not progress:
            progress = Progress(user_id=user_id, guessed_states="[]", high_score=0)
            db.session.add(progress)
            db.session.commit()

        try:
            guessed_states = json.loads(progress.guessed_states or "[]")
        except (json.JSONDecodeError, TypeError):
            guessed_states = []

        return render_template("index.html", guessed_states=guessed_states)

    except Exception as e:
        print("GAME ERROR:", e)
        return "Something went wrong in /game", 500


# ---------- SAVE ----------
@app.route("/save_progress", methods=["POST"])
def save_progress():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 403

    data = request.get_json() or {}
    guessed_states = data.get("guessed_states", [])

    progress = Progress.query.filter_by(user_id=session["user_id"]).first()

    if not progress:
        progress = Progress(user_id=session["user_id"], guessed_states="[]", high_score=0)
        db.session.add(progress)

    # Always update guessed states and high score for all users
    progress.guessed_states = json.dumps(guessed_states or [])
    score = len(guessed_states)
    if score > progress.high_score:
        progress.high_score = score

    db.session.commit()
    return jsonify({"status": "ok"})


# ---------- LEADERBOARD ----------
@app.route("/leaderboard")
def leaderboard():
    top_users = (
        db.session.query(User.username, Progress.high_score)
        .join(Progress, User.id == Progress.user_id)
        .order_by(Progress.high_score.desc())
        .limit(10)
        .all()
    )

    return render_template("leaderboard.html", top_users=top_users)


# ---------- PROFILE ----------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    try:
        user = db.session.get(User, session["user_id"])  # Fixed: no longer deprecated

        if not user:
            return redirect("/login")

        progress = Progress.query.filter_by(user_id=user.id).first()
        high_score = progress.high_score if progress else 0

        return render_template(
            "profile.html",
            username=user.username,
            email=user.email,
            high_score=high_score
        )

    except Exception as e:
        print("PROFILE ERROR:", e)
        return "Something went wrong", 500


# ---------- RESET ----------
@app.route("/reset", methods=["POST"])
def reset_game():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 403

    progress = Progress.query.filter_by(user_id=session["user_id"]).first()
    if progress:
        progress.guessed_states = "[]"
        db.session.commit()

    return jsonify(success=True)


# ---------- STATE ----------
@app.route("/state/<state_name>")
def show_description(state_name):
    return render_template("state.html", state_name=state_name.title())


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run()