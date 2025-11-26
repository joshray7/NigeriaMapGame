from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import json
import os
import jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "d0bbf985f0efc162da04980e2746a4e9f2bc1c6818ccde32c4e3fc9a54849eec")


# ==========================
#   DATABASE CONFIGURATION
# ==========================

# Use Render DATABASE_URL if available
DATABASE_URL = os.getenv("DATABASE_URL")

# If running locally → use your local PostgreSQL or fallback to SQLite
if not DATABASE_URL:
    print("⚠ Using LOCAL database instead of Render DATABASE_URL")
    DATABASE_URL = "sqlite:///local.db"

# Apply configuration BEFORE initializing SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# ==========================
#        MODELS
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    guessed_states = db.Column(db.Text)  # JSON
    high_score = db.Column(db.Integer, default=0)


# Create tables automatically
with app.app_context():
    db.create_all()


# ==========================
#         ROUTES
# ==========================

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/game')
    else:
        return redirect('/login')



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

        p = Progress(user_id=user.id, guessed_states="[]")
        db.session.add(p)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")


# -------- LOGIN --------
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

    user_id = session["user_id"]
    progress = Progress.query.filter_by(user_id=user_id).first()

    # If user has no progress entry — create one
    if progress is None:
        progress = Progress(user_id=user_id, guessed_states="[]", high_score=0)
        db.session.add(progress)
        db.session.commit()

    guessed_states = json.loads(progress.guessed_states)


    return render_template("index.html", guessed_states=guessed_states)


# ---------- SAVE PROGRESS ----------
@app.route("/save_progress", methods=["POST"])
def save_progress():
    if "user_id" not in session:
        return "Not logged in", 403

    data = request.get_json()
    guessed_states = data["guessed_states"]

    progress = Progress.query.filter_by(user_id=session["user_id"]).first()
    progress.guessed_states = json.dumps(guessed_states)
    db.session.commit()

    return "OK", 200


@app.route('/reset', methods=['POST'])
def reset_game():
    session.pop('guessed_states', None)
    return jsonify(success=True)

@app.route('/state/<state_name>')
def show_description(state_name):
    return render_template('state.html', state_name=state_name.title())

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
