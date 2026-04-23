from flask import render_template, request, redirect, url_for, flash, session
from services.rbac import has_permission
from . import school_timings_bp
from .services import (
    get_all_timings,
    create_timing,
    can_delete_timing,
    soft_delete_timing,
    get_active_session
)


def superintendent_only():
    return has_permission("school_timings.manage")


@school_timings_bp.route("/")
def index():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    timings = get_all_timings()
    active_session = get_active_session()

    return render_template(
        "school_timings/index.html",
        timings=timings,
        active_session=active_session
    )


@school_timings_bp.route("/create", methods=["POST"])
def create():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    try:
        create_timing(
            request.form.get("day_type"),
            request.form.get("reporting_time"),
            request.form.get("recess_time"),
            request.form.get("dispersal_senior"),
            request.form.get("dispersal_junior")
        )
        flash("School timing added successfully", "success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("school_timings.index"))


@school_timings_bp.route("/delete/<int:timing_id>")
def delete(timing_id):
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    ok, msg = can_delete_timing(timing_id)
    if not ok:
        flash(msg, "danger")
        return redirect(url_for("school_timings.index"))

    soft_delete_timing(timing_id)
    flash("School timing deleted safely", "success")
    return redirect(url_for("school_timings.index"))
