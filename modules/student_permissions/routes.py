from flask import (
    render_template, request, redirect,
    url_for, flash, session
)
from services.rbac import has_permission

from . import student_permissions_bp
from models.db import get_db

# ✅ Student data must come ONLY from Student Master
from modules.student_master.services import get_student_full_by_ledger

from .services import (
    save_permission_file,
    get_self_going_history,
    get_device_history,
    revoke_self_going,
    revoke_device,
    get_active_self_going,
    get_active_device_permission,
    get_permission_dashboard_metrics,
    get_recent_permission_activity
)


# --------------------------------------------------
# ACCESS CONTROL
# --------------------------------------------------
def superintendent_only():
    return has_permission("student_permissions.manage")


# --------------------------------------------------
# MODULE HOME
# --------------------------------------------------
@student_permissions_bp.route("/")
def index():
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    return render_template(
        "student_permissions/index.html",
        metrics=get_permission_dashboard_metrics(),
        recent_activity=get_recent_permission_activity()
    )


# --------------------------------------------------
# SELF GOING PERMISSION
# --------------------------------------------------
@student_permissions_bp.route("/self-going", methods=["GET", "POST"])
def self_going():
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    ledger = request.args.get("ledger_no")
    data = get_student_full_by_ledger(ledger) if ledger else None
    student = data["student"] if data else None

    if request.method == "POST":
        ledger = request.form.get("ledger_no")
        data = get_student_full_by_ledger(ledger)
        student = data["student"] if data else None

        if not student:
            flash("Invalid Ledger Number", "danger")
            return redirect(request.url)

        file_path = save_permission_file(
            request.files.get("application_file"),
            ledger,
            "self_going"
        )

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO student_self_going
            (student_id, allowed, valid_from, valid_to, application_file, remarks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student["id"],
            int(request.form.get("allowed")),
            request.form.get("valid_from"),
            request.form.get("valid_to"),
            file_path,
            request.form.get("remarks")
        ))
        db.commit()
        db.close()

        flash("Self Going permission saved successfully", "success")
        return redirect(
            url_for("student_permissions.self_going", ledger_no=ledger)
        )

    return render_template(
        "student_permissions/self_going.html",
        student=student,
        active_permission=get_active_self_going(student["id"]) if student else None,
        history=get_self_going_history(student["id"]) if student else []
    )


# --------------------------------------------------
# DEVICE PERMISSION
# --------------------------------------------------
@student_permissions_bp.route("/device", methods=["GET", "POST"])
def device_permission():
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    ledger = request.args.get("ledger_no")
    data = get_student_full_by_ledger(ledger) if ledger else None
    student = data["student"] if data else None

    if request.method == "POST":
        ledger = request.form.get("ledger_no")
        data = get_student_full_by_ledger(ledger)
        student = data["student"] if data else None

        if not student:
            flash("Invalid Ledger Number", "danger")
            return redirect(request.url)

        file_path = save_permission_file(
            request.files.get("application_file"),
            ledger,
            "device"
        )

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO student_device_permission
            (student_id, device_type, allowed, application_file, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, (
            student["id"],
            request.form.get("device_type"),
            int(request.form.get("allowed")),
            file_path,
            request.form.get("remarks")
        ))
        db.commit()
        db.close()

        flash("Device permission saved successfully", "success")
        return redirect(
            url_for("student_permissions.device_permission", ledger_no=ledger)
        )

    return render_template(
        "student_permissions/device_permission.html",
        student=student,
        active_permission=get_active_device_permission(student["id"]) if student else None,
        history=get_device_history(student["id"]) if student else []
    )


# --------------------------------------------------
# PERMISSION HISTORY (MASTER VIEW)
# --------------------------------------------------
@student_permissions_bp.route("/history")
def permission_history():
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    ledger = request.args.get("ledger_no")
    data = get_student_full_by_ledger(ledger) if ledger else None
    student = data["student"] if data else None

    history = {}
    if student:
        history["self_going"] = get_self_going_history(student["id"])
        history["device"] = get_device_history(student["id"])

    return render_template(
        "student_permissions/history.html",
        student=student,
        history=history,
        recent_activity=get_recent_permission_activity(12)
    )


# --------------------------------------------------
# REVOKE SELF GOING
# --------------------------------------------------
@student_permissions_bp.route("/revoke/self-going/<int:pid>", methods=["POST"])
def revoke_self(pid):
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    revoke_self_going(pid, request.form.get("reason"))
    flash("Self Going permission revoked", "warning")
    return redirect(request.referrer)


# --------------------------------------------------
# REVOKE DEVICE PERMISSION
# --------------------------------------------------
@student_permissions_bp.route("/revoke/device/<int:pid>", methods=["POST"])
def revoke_device_perm(pid):
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    revoke_device(pid, request.form.get("reason"))
    flash("Device permission revoked", "warning")
    return redirect(request.referrer)
