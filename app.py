from flask import Flask, render_template, current_app, session, request, flash, abort, redirect, escape
from werkzeug import exceptions
from loguru import logger
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session, SqlAlchemySessionInterface
from flask_migrate import Migrate
from typing import List, Dict
from utils.parser import parse_leaderboard, validate_leaderboard

db = SQLAlchemy()
sess = Session()
app = Flask(__name__)
app.config.from_pyfile("config.py")

migrate = Migrate(app, db)

# order matters https://stackoverflow.com/questions/46029406/do-i-need-to-create-a-sessions-table-to-use-flask-session-sqlalchemysessioninter
db.init_app(app)
migrate.init_app(app)
sess.init_app(app)
SqlAlchemySessionInterface(app, db, "sessions", "sess_")


# fmt: off
from models import User 
# fmt: on


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


def leaderboard_data(day: int):
    users: List[User] = User.query.all()

    leaderboard = {
        "show_day": day,
        "days": [],
        "data": []
    }

    # rank each user each day and then overall
    days = set()
    for user in users:
        if user.leaderboard == "":
            continue

        leaderboard_stats = parse_leaderboard(user.leaderboard)

        # TODO: this just puts people on the leaderboard, put them in the right
        #       order and rank them
        for day_stat in leaderboard_stats:
            days.add(day_stat["day"])

            if not day_stat["day"] == day:
                continue

            day_stat["user"] = user.user_name

            leaderboard["data"].append(day_stat)

    leaderboard["days"] = list(days)

    return leaderboard


@app.route("/")
def home():
    valid_session = validate_session()

    personal_leaderboard = None

    if valid_session:
        user: User = db.session.get(User, session["user_id"])
        personal_leaderboard = user.leaderboard

    global_leaderboard = leaderboard_data(1)
    global_leaderboard["show_title"] = True

    return render_template(
        "home.html",
        personal_leaderboard=personal_leaderboard,
        leaderboard=global_leaderboard)


@app.get("/leaderboard/day/<int:day>")
def get_leaderboard(day: int):
    logger.info(f'request for leaderboard day {day}')

    return render_template(
        "leaderboard.html", leaderboard=leaderboard_data(day))


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

    personal_leaderboard = escape(
        request.form["personal_leaderboard"].replace(">", ""))

    # validate the input here
    if not validate_leaderboard(personal_leaderboard):
        flash("leaderboard input was invalid try again")
        return redirect("/")

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


def error_handler(code: int = 500):
    if request.headers.get("Hx-Request"):
        return render_template("flash_message.html"), code

    return render_template("error.html"), 200


@app.errorhandler(404)
def not_authorized(e):
    logger.error(e)
    return error_handler(404)


@app.errorhandler(401)
def not_authorized(e):
    logger.error(e)
    return error_handler(401)


@app.errorhandler(422)
def bad_form_input(e):
    logger.error(e)
    return error_handler(422)


@app.errorhandler(exceptions.HTTPException)
def server_error(e):
    logger.error(e)
    return error_handler(500)


@app.errorhandler(Exception)
def generic_handler(e):
    logger.error(e)
    return error_handler(500)


@app.cli.command("init_db")
def init_db():
    db.create_all()
