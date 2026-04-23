import os
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from . import barber_haircut_bp
from .services import (
    create_haircut_record,
    get_monthly_done_list,
    get_defaulter_list,
    get_student_history,
    get_current_month,
    fetch_student_by_ledger
)


@barber_haircut_bp.route("/barber")
def barber_dashboard():
    month_key = request.args.get("month", get_current_month())
    done_list, month_key = get_monthly_done_list(month_key)
    defaulters, _, cutoff_active, cutoff_day = get_defaulter_list(month_key)
    return render_template(
        "barber_haircut/dashboard.html",
        done_list=done_list,
        month_key=month_key,
        defaulter_count=len(defaulters) if cutoff_active else 0,
        cutoff_active=cutoff_active,
        cutoff_day=cutoff_day,
    )


# ✅ NEW API: Ledger search auto-fill
@barber_haircut_bp.route("/barber/api/student/<ledger_no>")
def barber_api_student(ledger_no):
    student = fetch_student_by_ledger(ledger_no)
    if not student:
        return jsonify({"ok": False, "message": "Student not found"}), 404

    return jsonify({
        "ok": True,
        "ledger_no": student["ledger_no"],
        "student_name": student["student_name"],
        "class_name": student["class_name"],
        "section": student["section"],
        "status": student["status"]
    })


@barber_haircut_bp.route("/barber/media/<path:filename>")
def barber_media(filename):
    media_root = os.path.join(current_app.instance_path, "haircuts")
    return send_from_directory(media_root, filename)


@barber_haircut_bp.route("/barber/record", methods=["GET", "POST"])
def barber_record():
    prefill_ledger = request.args.get("ledger_no", "")
    if request.method == "POST":
        before_file = request.files.get("before_photo")
        after_file = request.files.get("after_photo")

        ok, msg = create_haircut_record(request.form, before_file, after_file)
        flash(msg, "success" if ok else "danger")

        if ok:
            return redirect(url_for("barber_haircut.barber_dashboard"))

    return render_template("barber_haircut/record.html", prefill_ledger=prefill_ledger)


@barber_haircut_bp.route("/barber/defaulters")
def barber_defaulters():
    month_key = request.args.get("month", get_current_month())
    defaulters, month_key, cutoff_active, cutoff_day = get_defaulter_list(month_key)
    return render_template(
        "barber_haircut/defaulters.html",
        defaulters=defaulters,
        month_key=month_key,
        cutoff_active=cutoff_active,
        cutoff_day=cutoff_day
    )


@barber_haircut_bp.route("/barber/history/<ledger_no>")
def barber_history(ledger_no):
    history = get_student_history(ledger_no)
    return render_template("barber_haircut/history.html", history=history, ledger_no=ledger_no)
