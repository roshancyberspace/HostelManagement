from flask import render_template, request, redirect, url_for, flash, session
from services.rbac import has_permission
from . import hostel_timetable_bp
from .services import (
    get_timetable,
    add_activity,
    update_activity,
    soft_delete_activity,
    get_active_session
)


def superintendent_only():
    return has_permission("hostel_timetable.manage")


@hostel_timetable_bp.route("/", methods=["GET", "POST"])
def index():
    if not superintendent_only():
        flash("Unauthorized", "danger")
        return redirect(url_for("dashboard"))

    day_type = request.args.get("day_type", "WORKING")
    active_session = get_active_session()

    if request.method == "POST":
        add_activity(
            day_type,
            request.form["activity_name"],
            request.form.get("start_time"),
            request.form.get("end_time"),
            request.form["time_source"],
            int(request.form["sequence_no"])
        )
        flash("Activity added", "success")
        return redirect(url_for("hostel_timetable.index", day_type=day_type))

    timetable = get_timetable(day_type)
    return render_template(
        "hostel_timetable/index.html",
        timetable=timetable,
        day_type=day_type,
        active_session=active_session
    )


@hostel_timetable_bp.route("/update/<int:row_id>", methods=["POST"])
def update(row_id):
    update_activity(
        row_id,
        request.form.get("start_time"),
        request.form.get("end_time"),
        int(request.form["sequence_no"])
    )
    flash("Activity updated", "success")
    return redirect(request.referrer)


@hostel_timetable_bp.route("/delete/<int:row_id>")
def delete(row_id):
    soft_delete_activity(row_id)
    flash("Activity deleted safely", "success")
    return redirect(request.referrer)
