from flask import render_template, request, redirect, url_for, flash, session
from models.db import get_db
from . import master_feed_bp
from services.rbac import has_permission
from .services import (
    get_all_routines,
    create_routine,
    can_delete_routine,
    soft_delete_routine,
    get_all_forms,
    create_form,
    can_delete_form,
    soft_delete_form
)

# =====================================================
# ROLE CHECK
# =====================================================

def superintendent_only():
    return has_permission("master_feed.manage")

# =====================================================
# MASTER FEED DASHBOARD (ROOT)
# URL: /master-feed/
# =====================================================

@master_feed_bp.route("/")
def master_feed_dashboard():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    # Role for UI visibility
    user_role = session["user"]["role"]

    modules = {
    "routines": True,
    "forms": True,
    "hostel_governance": has_permission("master_feed.manage")
}


    return render_template(
        "master_feed/dashboard.html",
        modules=modules,
        user_role=user_role
    )

# =====================================================
# ROUTINES
# =====================================================

@master_feed_bp.route("/routines", methods=["GET", "POST"])
def routines():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        if not title:
            flash("Routine title is required", "danger")
            return redirect(url_for("master_feed.routines"))

        create_routine(title, description)
        flash("Routine added successfully", "success")
        return redirect(url_for("master_feed.routines"))

    routines = get_all_routines()
    return render_template("master_feed/routines.html", routines=routines)


@master_feed_bp.route("/routines/delete/<int:routine_id>")
def delete_routine(routine_id):
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    ok, msg = can_delete_routine(routine_id)
    if not ok:
        flash(msg, "danger")
        return redirect(url_for("master_feed.routines"))

    soft_delete_routine(routine_id)
    flash("Routine deleted safely", "success")
    return redirect(url_for("master_feed.routines"))

# =====================================================
# FORMS
# =====================================================

@master_feed_bp.route("/forms", methods=["GET", "POST"])
def forms():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        form_name = request.form.get("form_name")
        target_url = request.form.get("target_url")

        if not form_name or not target_url:
            flash("All fields are required", "danger")
            return redirect(url_for("master_feed.forms"))

        create_form(form_name, target_url)
        flash("Form registered successfully", "success")
        return redirect(url_for("master_feed.forms"))

    forms = get_all_forms()
    return render_template("master_feed/forms.html", forms=forms)


@master_feed_bp.route("/forms/delete/<int:form_id>")
def delete_form(form_id):
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    ok, msg = can_delete_form(form_id)
    if not ok:
        flash(msg, "danger")
        return redirect(url_for("master_feed.forms"))

    soft_delete_form(form_id)
    flash("Form deleted safely", "success")
    return redirect(url_for("master_feed.forms"))

# =====================================================
# ROUTINE LOGS
# URL: /master-feed/routine-logs
# =====================================================

@master_feed_bp.route("/routine-logs")
def routine_logs():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()

    # ✅ latest 300 logs
    logs = db.execute("""
        SELECT *
        FROM routine_logs
        ORDER BY id DESC
        LIMIT 300
    """).fetchall()

    return render_template("master_feed/routine_logs.html", logs=logs)
