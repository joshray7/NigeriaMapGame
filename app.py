from flask import Flask, render_template, request, redirect,  session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import json

app = Flask(__name__)
app.secret_key = "d0bbf985f0efc162da04980e2746a4e9f2bc1c6818ccde32c4e3fc9a54849eec"

# ==========================
#   MYSQL DATABASE SETUP
# ==========================
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Joshray777.()@localhost/nigeria_game"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ==========================
#   DATABASE MODELS
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
    guessed_states = db.Column(db.Text)  # JSON array
    high_score = db.Column(db.Integer, default=0)

# Create tables
with app.app_context():
    db.create_all()

# ==========================
#          ROUTES
# ==========================

@app.route("/")
def index():
    return redirect("/signup")


# ------- SIGNUP -------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        if username is None:
        # Handle missing username
            return "Username is required", 400
        email = request.form["email"]
        password = request.form["password"]

        # Check if user exists
        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            return render_template("signup.html", error="User already exists.")

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(username=username, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()

        # Automatically create progress entry
        p = Progress(user_id=user.id, guessed_states="[]")
        db.session.add(p)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")


# ------- LOGIN -------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.verify_password(password):
            # Save user in session
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect("/game")

        error = "Invalid username or password."

    return render_template("login.html", error=error)


# ------------ GAME PAGE -------------
@app.route("/game")
def game():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # Load their progress
    progress = Progress.query.filter_by(user_id=user_id).first()

    guessed_states = json.loads(progress.guessed_states)

    return render_template("index.html", guessed_states=guessed_states)


# -------- SAVE PROGRESS (AJAX) --------
@app.route("/save_progress", methods=["POST"])
def save_progress():
    if "user_id" not in session:
        return "Not logged in", 403

    user_id = session["user_id"]

    data = request.get_json()
    guessed_states = data["guessed_states"]

    progress = Progress.query.filter_by(user_id=user_id).first()
    progress.guessed_states = json.dumps(guessed_states)

    db.session.commit()

    return "OK", 200


# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
