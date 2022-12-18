from flask import Flask, render_template, current_app, session, request, flash, abort, redirect, escape
from urllib.parse import urlencode
from werkzeug import exceptions
from loguru import logger
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session, SqlAlchemySessionInterface
from flask_migrate import Migrate
from typing import List, Dict
from utils.parser import parse_leaderboard, validate_leaderboard
from requests import post, get

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


def validate_session(check_admin=False) -> bool:
    if not "user_name" in session:
        return False

    if "user_name" in session or "user_id" in session:
        user: User = db.session.get(User, session["user_id"])

        if not user:
            session.pop("user_id")
            session.pop("user_name")
            return False

        admin_emails = app.config["ADMIN_EMAILS"].split(",")

        if (not user.email in admin_emails) and check_admin:
            logger.error(f'user {user.email} tried to access admin panel')
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
def index():
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
    # create the request
    url = "https://github.com/login/oauth/authorize"

    params = {
        "client_id": app.config["GITHUB_CLIENT_ID"],
        "scope": "user",
    }

    url = url + "?" + urlencode(params)

    logger.info(f'redirecting to {url}')

    return redirect(url)


@app.post("/logout")
def logout():
    # delete the github token from the user and the session
    if "user_id" in session:
        user: User = db.session.get(User, session["user_id"])

        if user:
            user.github_access_token = ""
            db.session.commit()

    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("github_access_token", None)

    return redirect("/")


@app.get("/api/auth/callback/github")
def get_auth_handler():
    args = request.args

    if not "code" in args:
        logger.error("code did not get sent in args")
        flash("error authenticating you")
        return redirect("/")

    temp_auth_code = args["code"]

    url = "https://github.com/login/oauth/access_token"

    params = {
        "client_id": app.config["GITHUB_CLIENT_ID"],
        "client_secret": app.config["GITHUB_CLIENT_SECRET"],
        "code": temp_auth_code,
    }

    url = url + "?" + urlencode(params)

    res = post(url, headers={
        "Accept": "application/json"
    })

    if res.status_code > 299 or res.status_code < 200:
        logger.error(f'oauth access_token request failed [{res.status_code}]')
        flash("error authenticating you")
        return redirect("/")

    json_response = res.json()

    if not "access_token" in json_response:
        logger.error("no access_token in github oauth response")
        flash("error authenticating you")
        return redirect("/")

    access_token = json_response["access_token"]

    user_info = get("https://api.github.com/user", headers={
        "Authorization": "Bearer " + access_token,
        "Accept": "application/json",
    })

    if user_info.status_code > 299 or user_info.status_code < 200:
        logger.error(f'getting user info failed [{user_info.status_code}]')
        flash("error authenticating you")
        return redirect("/")

    user_emails = get("https://api.github.com/user/emails", headers={
        "Authorization": "Bearer " + access_token,
        "Accept": "application/json",
    })

    if user_emails.status_code > 299 or user_emails.status_code < 200:
        logger.error(f'getting user emails failed [{user_emails.status_code}]')
        flash("error authenticating you")
        return redirect("/")

    user_primary_email = list(
        filter(lambda e: e["primary"], user_emails.json()))[0]["email"]

    logger.info(f'user_email = {user_primary_email}')

    session["github_access_token"] = access_token
    user_info_obj = user_info.json()

    existing_user = User.query.filter_by(
        user_name=user_info_obj["login"]).first()

    if not existing_user:
        new_user = User(
            user_name=user_info_obj["login"],
            email=user_primary_email,
            github_access_token=access_token)
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        session["user_name"] = new_user.user_name
        logger.info(f'created new user with email {new_user.email}')
    else:
        session["user_id"] = existing_user.id
        session["user_name"] = existing_user.user_name
        logger.info(f'logged in existing_user {existing_user.user_name}')

    return redirect("/")


@app.get("/admin")
def admin_route():
    if not validate_session(check_admin=True):
        flash("you are not an admin")
        return redirect("/")

    users = User.query.all()

    return render_template("admin_panel.html",
                           users=users)


@app.delete("/admin/user")
def delete_user():
    logger.info("here")
    if not validate_session(check_admin=True):
        flash("you are not an admin")
        return redirect("/")

    user_id = request.args.get("user_id", None)

    if not user_id:
        flash("that user does not exist")
        return redirect("/admin")

    User.query.filter_by(id=user_id).delete()
    db.session.commit()

    users = User.query.all()

    return render_template("admin_user_list.html",
                           users=users)


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
