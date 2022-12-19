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


# fmt: off
from blueprints.auth import bp as auth_bp
from blueprints.leaderboard import bp as leaderboard_bp
from blueprints.admin import bp as admin_bp
# fmt: on


app.register_blueprint(leaderboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)


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
