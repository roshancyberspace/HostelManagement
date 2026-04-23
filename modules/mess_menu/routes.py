from flask import render_template, request, redirect, url_for, flash, session
from services.rbac import has_permission
from . import mess_menu_bp
from .services import (
    get_active_weekly_menu,
    create_new_weekly_menu,
    save_weekly_menu,
    DAYS
)


def superintendent_only():
    return has_permission("mess_menu.manage")


@mess_menu_bp.route("/", methods=["GET", "POST"])
def weekly_menu():
    if not superintendent_only():
        flash("Unauthorized", "danger")
        return redirect(url_for("dashboard"))

    day_type = request.args.get("day_type", "WORKING")

    header, items = get_active_weekly_menu(day_type)

    if request.method == "POST":
        if "create_new" in request.form:
            create_new_weekly_menu(day_type, request.form.get("title"))
            flash("New weekly menu created", "success")
            return redirect(url_for("mess_menu.weekly_menu", day_type=day_type))

        if header:
            save_weekly_menu(header["id"], request.form)
            flash("Menu updated successfully", "success")

    return render_template(
        "mess_menu/weekly_menu.html",
        day_type=day_type,
        header=header,
        items=items,
        days=DAYS,
        item_count=len(items),
        brunch_enabled=day_type == "WORKING",
    )
