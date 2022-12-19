from flask import Blueprint, flash, redirect, render_template, request, session, current_app, escape, abort
from app import db, logger, validate_session
from utils.parser import parse_leaderboard, validate_leaderboard
from models import User

bp = Blueprint("leaderboard", __name__)


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


@bp.route("/")
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


@bp.get("/leaderboard/day/<int:day>")
def get_leaderboard(day: int):
    logger.info(f'request for leaderboard day {day}')

    return render_template(
        "leaderboard.html", leaderboard=leaderboard_data(day))


@bp.post("/user/leaderboard")
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
