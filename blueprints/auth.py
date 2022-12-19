from flask import Blueprint, flash, redirect, render_template, request, session, current_app
from requests import get, post
from urllib.parse import urlencode
from app import db, logger
from models import User

bp = Blueprint("auth", __name__)


# technically this is login and signup for now
@bp.post("/login")
def login():
    # create the request
    url = "https://github.com/login/oauth/authorize"

    params = {
        "client_id": current_app.config["GITHUB_CLIENT_ID"],
        "scope": "user",
    }

    url = url + "?" + urlencode(params)

    logger.info(f'redirecting to {url}')

    return redirect(url)


@bp.post("/logout")
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


@bp.get("/api/auth/callback/github")
def get_auth_handler():
    args = request.args

    if not "code" in args:
        logger.error("code did not get sent in args")
        flash("error authenticating you")
        return redirect("/")

    temp_auth_code = args["code"]

    url = "https://github.com/login/oauth/access_token"

    params = {
        "client_id": current_app.config["GITHUB_CLIENT_ID"],
        "client_secret": current_app.config["GITHUB_CLIENT_SECRET"],
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
