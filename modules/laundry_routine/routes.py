from flask import render_template, request, redirect, url_for, flash, session
from services.rbac import has_permission
from . import laundry_routine_bp
from .services import (
    get_active_laundry_routine,
    create_laundry_routine,
    save_laundry_routine,
    DAYS
)


def superintendent_only():
    return has_permission("laundry.manage")


@laundry_routine_bp.route("/", methods=["GET", "POST"])
def weekly_routine():
    if not superintendent_only():
        flash("Unauthorized", "danger")
        return redirect(url_for("dashboard"))

    header, rows = get_active_laundry_routine()

    if request.method == "POST":
        if "create_new" in request.form:
            create_laundry_routine(request.form.get("title"))
            flash("Laundry routine created", "success")
            return redirect(url_for("laundry_routine.weekly_routine"))

        if header:
            save_laundry_routine(header["id"], request.form)
            flash("Laundry routine updated", "success")

    return render_template(
        "laundry_routine/weekly_routine.html",
        header=header,
        rows=rows,
        days=DAYS
    )
