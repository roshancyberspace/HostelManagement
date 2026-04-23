import os
import csv
from flask import render_template, request, redirect, url_for, flash, send_file
from .services import (
    ensure_daily_sheet,
    get_daily_coaching_rows,
    get_daily_study_rows,
    update_coaching_row,
    update_study_row,
    get_day_name_from_date,
    get_coaching_weekly_master,
    get_study_weekly_master,
    update_weekly_coaching_row,
    update_weekly_study_row,
    bulk_suspend_weekly,
)
from .pdf_service import generate_coaching_pdf, generate_self_study_pdf
from . import coaching_daily_sheet_bp


# ==========================================================
# DAILY ROUTES
# ==========================================================
@coaching_daily_sheet_bp.route("/coaching/daily", methods=["GET", "POST"])
def daily_home():
    if request.method == "POST":
        sheet_date = request.form.get("sheet_date")
        if not sheet_date:
            flash("❌ Please select a valid date.", "danger")
            return redirect(url_for("coaching_daily_sheet.daily_home"))

        ensure_daily_sheet(sheet_date, created_by="ADMIN")
        return redirect(url_for("coaching_daily_sheet.daily_edit", date_str=sheet_date))

    return render_template("coaching_daily_sheet/daily_home_premium.html")


@coaching_daily_sheet_bp.route("/coaching/daily/<date_str>/edit", methods=["GET", "POST"])
def daily_edit(date_str):
    day_name = ensure_daily_sheet(date_str, created_by="ADMIN")

    coaching_rows = get_daily_coaching_rows(date_str)
    study_rows = get_daily_study_rows(date_str)

    if request.method == "POST":
        if request.form.get("update_type") == "coaching":
            row_id = int(request.form.get("row_id"))
            ok, msg = update_coaching_row(row_id, request.form, updated_by="ADMIN")
            flash(msg, "success" if ok else "danger")
            return redirect(url_for("coaching_daily_sheet.daily_edit", date_str=date_str))

        if request.form.get("update_type") == "study":
            row_id = int(request.form.get("row_id"))
            ok, msg = update_study_row(row_id, request.form, updated_by="ADMIN")
            flash(msg, "success" if ok else "danger")
            return redirect(url_for("coaching_daily_sheet.daily_edit", date_str=date_str))

    return render_template(
        "coaching_daily_sheet/daily_edit.html",
        date_str=date_str,
        day_name=day_name,
        coaching_rows=coaching_rows,
        study_rows=study_rows
    )


@coaching_daily_sheet_bp.route("/coaching/daily/<date_str>/print-coaching")
def print_coaching(date_str):
    ensure_daily_sheet(date_str, created_by="ADMIN")
    day_name = get_day_name_from_date(date_str)

    coaching_rows = get_daily_coaching_rows(date_str)

    coaching_list = []
    for r in coaching_rows:
        coaching_list.append({
            "class_name": r["class_name"],
            "subject": r["subject"],
            "start_time": r["start_time"],
            "end_time": r["end_time"],
            "teacher_name": r["teacher_name"],
            "status": r["status"],
            "remark": r["remark"]
        })

    out_dir = "generated_pdfs"
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, f"Coaching_{date_str}.pdf")

    generate_coaching_pdf(filepath, date_str, day_name, coaching_list)
    return send_file(filepath, as_attachment=True)


@coaching_daily_sheet_bp.route("/coaching/daily/<date_str>/print-study")
def print_study(date_str):
    ensure_daily_sheet(date_str, created_by="ADMIN")
    day_name = get_day_name_from_date(date_str)

    study_rows = get_daily_study_rows(date_str)

    study_list = []
    for r in study_rows:
        study_list.append({
            "class_group": r["class_group"],
            "floor_place": r["floor_place"],
            "teacher_name": r["teacher_name"],
            "start_time": r["start_time"],
            "end_time": r["end_time"],
            "status": r["status"],
            "remark": r["remark"]
        })

    out_dir = "generated_pdfs"
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, f"SelfStudy_{date_str}.pdf")

    generate_self_study_pdf(filepath, date_str, day_name, study_list)
    return send_file(filepath, as_attachment=True)


# ==========================================================
# MASTER ROUTINE CONTROL PANEL
# ==========================================================
@coaching_daily_sheet_bp.route("/coaching/master")
def master_dashboard():
    return render_template("coaching_daily_sheet/master_dashboard.html")


@coaching_daily_sheet_bp.route("/coaching/master/coaching", methods=["GET", "POST"])
def master_coaching():
    if request.method == "POST":
        row_id = int(request.form.get("row_id"))
        ok, msg = update_weekly_coaching_row(row_id, request.form, updated_by="ADMIN")
        flash(msg, "success" if ok else "danger")
        return redirect(url_for("coaching_daily_sheet.master_coaching"))

    rows = get_coaching_weekly_master()
    return render_template("coaching_daily_sheet/master_coaching.html", rows=rows)


@coaching_daily_sheet_bp.route("/coaching/master/study", methods=["GET", "POST"])
def master_study():
    if request.method == "POST":
        row_id = int(request.form.get("row_id"))
        ok, msg = update_weekly_study_row(row_id, request.form, updated_by="ADMIN")
        flash(msg, "success" if ok else "danger")
        return redirect(url_for("coaching_daily_sheet.master_study"))

    rows = get_study_weekly_master()
    return render_template("coaching_daily_sheet/master_study.html", rows=rows)


@coaching_daily_sheet_bp.route("/coaching/master/suspend", methods=["GET", "POST"])
def master_suspend():
    if request.method == "POST":
        day_name = request.form.get("day_name")
        routine_type = request.form.get("routine_type")
        reason = request.form.get("reason")

        ok, msg = bulk_suspend_weekly(day_name, routine_type, reason, updated_by="ADMIN")
        flash(msg, "success" if ok else "danger")
        return redirect(url_for("coaching_daily_sheet.master_suspend"))

    return render_template("coaching_daily_sheet/master_suspend.html")


@coaching_daily_sheet_bp.route("/coaching/master/upload", methods=["GET", "POST"])
def master_upload():
    """
    Upload a CSV file to update weekly master.
    Format:
    COACHING CSV columns:
    day_name,class_name,subject,start_time,end_time,teacher_name,status
    """
    if request.method == "POST":
        file = request.files.get("file")
        routine_type = request.form.get("routine_type")

        if not file:
            flash("❌ Please upload a CSV file.", "danger")
            return redirect(url_for("coaching_daily_sheet.master_upload"))

        # Save temp
        temp_path = "temp_master_upload.csv"
        file.save(temp_path)

        imported = 0

        from models.db import get_db
        conn = get_db()
        cur = conn.cursor()

        with open(temp_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if routine_type == "COACHING":
                    cur.execute("""
                        INSERT INTO coaching_weekly_master
                        (day_name, class_name, subject, start_time, end_time, teacher_name, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row["day_name"], row["class_name"], row["subject"],
                        row["start_time"], row["end_time"], row["teacher_name"],
                        row.get("status", "ACTIVE")
                    ))
                    imported += 1

                elif routine_type == "STUDY":
                    cur.execute("""
                        INSERT INTO study_duty_weekly_master
                        (day_name, class_group, floor_place, teacher_name, start_time, end_time, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row["day_name"], row["class_group"], row["floor_place"],
                        row["teacher_name"], row["start_time"], row["end_time"],
                        row.get("status", "ACTIVE")
                    ))
                    imported += 1

        conn.commit()
        conn.close()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        flash(f"✅ Upload successful. Imported rows: {imported}", "success")
        return redirect(url_for("coaching_daily_sheet.master_dashboard"))

    return render_template("coaching_daily_sheet/master_upload.html")
