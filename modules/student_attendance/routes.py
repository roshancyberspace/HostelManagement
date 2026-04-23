from flask import render_template, request, redirect, url_for, flash
from datetime import date
from modules.student_attendance import student_attendance_bp
from modules.student_attendance.services import (
    fetch_active_students,
    mark_attendance,
    get_slots_for_day,
    get_absent_students,
    get_active_classes,
    get_slot_summary,
    get_strength_count,
    get_attendance_status_totals
)

# ==================================================
# SELECT DATE & SLOT
# ==================================================

@student_attendance_bp.route("/", methods=["GET"])
def select_session():
    today = date.today()
    return render_template(
        "student_attendance/select_session.html",
        today=today,
        slots=get_slots_for_day(today),
        class_options=get_active_classes()
    )


# ==================================================
# LOAD STUDENTS FOR MARKING
# ==================================================

@student_attendance_bp.route("/load", methods=["GET"])
def load_students():
    att_date = date.fromisoformat(request.args["attendance_date"])
    slot = request.args["slot"]
    class_filter = request.args.get("class")

    filters = {}
    if class_filter:
        filters["class"] = class_filter

    students = fetch_active_students(filters)

    return render_template(
        "student_attendance/mark_attendance.html",
        attendance_date=att_date,
        slot=slot,
        students=students,
        class_filter=class_filter or ""
    )


# ==================================================
# SAVE ATTENDANCE
# ==================================================

@student_attendance_bp.route("/mark", methods=["POST"])
def mark():
    att_date = date.fromisoformat(request.form["attendance_date"])
    slot = request.form["slot"]

    ledger_nos = request.form.getlist("ledger_no")
    saved_count = 0

    for ledger_no in ledger_nos:
        status = request.form.get(f"status_{ledger_no}", "").strip()
        remarks = request.form.get(f"remarks_{ledger_no}", "").strip()

        if not status:
            continue

        mark_attendance(
            ledger_no=ledger_no,
            att_date=att_date,
            slot=slot,
            status=status,
            marked_by="Superintendent",
            remarks=remarks,
            captured_photo_data=request.form.get(f"captured_photo_{ledger_no}", "").strip()
        )
        saved_count += 1

    if saved_count == 0:
        flash("Select at least one student status before saving attendance.", "warning")
        return redirect(url_for("student_attendance.load_students", attendance_date=att_date.isoformat(), slot=slot))

    flash(f"Attendance saved for {saved_count} student(s).", "success")
    return redirect(url_for("student_attendance.dashboard", slot=slot, date=att_date.isoformat()))


# ==================================================
# ATTENDANCE DASHBOARD (SUPERINTENDENT)
# ==================================================

@student_attendance_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """
    Live attendance dashboard.
    Shows absent list for selected slot.
    """
    att_date = date.fromisoformat(request.args.get("date", date.today().isoformat()))
    slot = request.args.get("slot", "MORNING")

    absentees = get_absent_students(att_date, slot)
    summary = get_slot_summary(att_date, slot)
    strength = get_strength_count(att_date, slot)
    totals = get_attendance_status_totals(att_date, slot)

    return render_template(
        "student_attendance/dashboard.html",
        attendance_date=att_date,
        slot=slot,
        absentees=absentees,
        summary=summary,
        strength=strength,
        totals=totals,
        slots=get_slots_for_day(att_date)
    )

from modules.student_attendance.services import (
    get_daily_management_report,
    get_slot_total
)

@student_attendance_bp.route("/management-report", methods=["GET", "POST"])
def management_report():
    """
    Daily attendance report for management.
    """
    att_date = request.form.get("attendance_date")

    if att_date:
        att_date = date.fromisoformat(att_date)
    else:
        att_date = date.today()

    report = get_daily_management_report(att_date)

    morning_total = get_slot_total(att_date, "MORNING")
    night_total = get_slot_total(att_date, "NIGHT")

    mismatch = morning_total != night_total

    return render_template(
        "student_attendance/management_report.html",
        attendance_date=att_date,
        report=report,
        morning_total=morning_total,
        night_total=night_total,
        mismatch=mismatch
    )
