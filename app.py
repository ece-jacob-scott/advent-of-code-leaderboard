from flask import Flask, render_template, current_app, session, request, flash, abort, redirect, escape
from werkzeug import exceptions
from loguru import logger
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

db = SQLAlchemy()
sess = Session()
app = Flask(__name__)
app.config.from_pyfile("config.py")
db.init_app(app)
sess.init_app(app)


class User(db.Model):
    __tablename__ = "users"
    id: int = db.Column(db.Integer, primary_key=True)
    user_name: str = db.Column(db.String(120), unique=True)
    leaderboard: str = db.Column(db.Text())

    def __init__(self, user_name=None):
        self.user_name = user_name
        self.leaderboard = ""

    def __repr__(self):
        return f'<Entry {self.user_name!r}>'


def validate_session() -> bool:
    if not "user_name" in session:
        return False

    if "user_name" in session or "user_id" in session:
        user: User = db.session.get(User, session["user_id"])

        if not user:
            session.pop("user_id")
            session.pop("user_name")
            return False

    return True


@app.route("/")
def hello_world():
    valid_session = validate_session()

    personal_leaderboard = None

    if valid_session:
        user: User = db.session.get(User, session["user_id"])
        personal_leaderboard = user.leaderboard

    return render_template("home.html", personal_leaderboard=personal_leaderboard)


@app.post("/user/leaderboard")
def user_leaderboard():
    valid_session = validate_session()

    if not valid_session:
        flash("you do not have a valid session please login")
        return redirect("/")

    if not "personal_leaderboard" in request.form or not request.form["personal_leaderboard"]:
        flash("leaderboard form was empty")
        return redirect("/")

    user: User = db.session.get(User, session["user_id"])

    if not user:
        logger.error(
            f'look up for user_name {session["user_id"]} did not find a user')

        flash("something went wrong, tell Jacob to check the logs")
        abort(500)
        return

    personal_leaderboard = escape(request.form["personal_leaderboard"])

    logger.info(personal_leaderboard)

    user.leaderboard = personal_leaderboard.strip()

    db.session.commit()

    return redirect("/")


@app.get("/login")
def login_form():
    return render_template("login_inline.html")


# technically this is login and signup for now
@app.post("/login")
def login():
    if not "user_name" in request.form or not request.form["user_name"]:
        # how to handle this error?
        flash("form was submitted empty")
        abort(422)
        return

    user_name = request.form["user_name"]

    user = User.query.filter_by(user_name=user_name).first()

    if not user:
        new_user = User(user_name=user_name)

        db.session.add(new_user)
        db.session.commit()

    user: User = User.query.filter_by(user_name=user_name).first()

    session["user_id"] = user.id
    session["user_name"] = user.user_name

    return redirect("/")


@app.errorhandler(404)
def not_authorized(e):
    logger.error(e)
    return render_template("flash_message.html"), 401


@app.errorhandler(401)
def not_authorized(e):
    logger.error(e)
    return render_template("flash_message.html"), 401


@app.errorhandler(422)
def bad_form_input(e):
    logger.error(e)
    return render_template("flash_message.html"), 422


@app.errorhandler(exceptions.HTTPException)
def server_error(e):
    logger.error(e)
    return render_template("flash_message.html"), 500


@app.errorhandler(Exception)
def generic_handler(e):
    logger.error(e)
    return render_template("flash_message.html"), 500


@app.cli.command("init_db")
def init_db():
    db.create_all()
