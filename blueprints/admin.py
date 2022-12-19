from flask import Blueprint, flash, redirect, render_template, request, session, current_app, escape, abort
from app import db, logger, validate_session
from models import User

bp = Blueprint("admin", __name__)


@bp.get("/admin")
def admin_route():
    if not validate_session(check_admin=True):
        flash("you are not an admin")
        return redirect("/")

    users = User.query.all()

    return render_template("admin_panel.html",
                           users=users)


@bp.delete("/admin/user")
def delete_user():
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
