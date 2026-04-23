from flask import render_template, request, redirect, url_for, flash, session
from services.rbac import has_permission
from . import academic_session_bp
from .services import (
    get_all_sessions,
    get_active_session,
    create_session,
    can_delete_session,
    soft_delete_session
)


def superintendent_only():
    return has_permission("academic_session.manage")


@academic_session_bp.route("/")
def index():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    sessions = get_all_sessions()
    active_session = get_active_session()

    return render_template(
        "academic_session/index.html",
        sessions=sessions,
        active_session=active_session
    )


@academic_session_bp.route("/create", methods=["POST"])
def create():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    name = request.form.get("name")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    if not name or not start_date or not end_date:
        flash("All fields are required", "danger")
        return redirect(url_for("academic_session.index"))

    create_session(name, start_date, end_date)
    flash(f"Academic Session {name} activated", "success")
    return redirect(url_for("academic_session.index"))


@academic_session_bp.route("/delete/<int:session_id>")
def delete_session(session_id):
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    ok, msg = can_delete_session(session_id)
    if not ok:
        flash(msg, "danger")
        return redirect(url_for("academic_session.index"))

    soft_delete_session(session_id)
    flash("Session deleted safely", "success")
    return redirect(url_for("academic_session.index"))
