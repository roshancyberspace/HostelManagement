from flask import render_template, request, session, redirect, url_for, flash
from services.rbac import has_permission
from . import daily_schedule_bp
from .services import build_daily_schedule
from datetime import datetime


def superintendent_only():
    return has_permission("daily_schedule.view")


@daily_schedule_bp.route("/")
def index():
    if not superintendent_only():
        flash("Unauthorized", "danger")
        return redirect(url_for("dashboard"))

    day_type = request.args.get("day_type", "WORKING")

    weekday = datetime.today().strftime("%A").upper()
    schedule = build_daily_schedule(day_type, weekday)
    meal_count = sum(1 for row in schedule if row["has_menu"])
    first_item = schedule[0]["time"] if schedule else "Not available"

    return render_template(
        "daily_schedule/index.html",
        schedule=schedule,
        day_type=day_type,
        weekday=weekday,
        meal_count=meal_count,
        first_item=first_item,
        today=datetime.today().strftime("%d %B %Y"),
    )
@daily_schedule_bp.route("/print")
def print_view():
    if "user" not in session:
        return redirect(url_for("dashboard"))

    day_type = request.args.get("day_type", "WORKING")

    from datetime import datetime
    weekday = datetime.today().strftime("%A").upper()

    schedule = build_daily_schedule(day_type, weekday)
    meal_count = sum(1 for row in schedule if row["has_menu"])

    return render_template(
        "daily_schedule/print.html",
        schedule=schedule,
        day_type=day_type,
        weekday=weekday,
        today=datetime.today().strftime("%d %B %Y"),
        meal_count=meal_count,
    )
