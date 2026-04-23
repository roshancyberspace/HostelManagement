import io, csv
import os
from flask import (
    render_template, request, redirect,
    url_for, flash, session, send_file, send_from_directory, current_app
)
from services.rbac import has_permission

from . import student_master_bp
from models.db import get_db

from .services import (
    bulk_add_students,
    delete_student_record,
    get_student_full_by_ledger,
    save_biodata,
    generate_basic_student_excel,
    generate_full_biodata_excel,
    change_student_status,
    get_student_bed_info,
    get_student_permissions,
    generate_basic_student_bulk_excel   # NEW
)

from .services_excel import (
    process_biodata_excel,
    process_basic_student_excel         # NEW
)


# --------------------------------------------------
# ACCESS CONTROL
# --------------------------------------------------
def superintendent_only():
    return has_permission("students.manage")


# --------------------------------------------------
# STUDENT INTAKE DASHBOARD
# --------------------------------------------------
@student_master_bp.route("/intake")
def intake_dashboard():
    if not superintendent_only():
        return redirect(url_for("dashboard.dashboard"))
    return render_template("student_master/intake_dashboard.html")


@student_master_bp.route("/media/<path:filename>")
def student_media(filename):
    media_root = os.path.join(current_app.instance_path, "student_uploads")
    return send_from_directory(media_root, filename)


# --------------------------------------------------
# CSV BULK UPLOAD (LEGACY – KEPT)
# --------------------------------------------------
@student_master_bp.route("/bulk", methods=["GET", "POST"])
def bulk_upload():
    if not superintendent_only():
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        file = request.files["file"]
        reader = csv.DictReader(io.StringIO(file.stream.read().decode("UTF8")))
        rows = [{
            "ledger_no": r.get("Ledger Number"),
            "name": r.get("Student Name"),
            "class": r.get("Class"),
            "section": None
        } for r in reader]

        bulk_add_students(rows)
        flash("Students uploaded successfully (CSV)", "success")
        return redirect(url_for("student_master.intake_dashboard"))

    return render_template("student_master/bulk_upload.html")


# --------------------------------------------------
# EXCEL BULK UPLOAD (NEW – RECOMMENDED)
# --------------------------------------------------
@student_master_bp.route("/download/basic-bulk-excel")
def download_basic_bulk_excel():
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    wb = generate_basic_student_bulk_excel()
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        download_name="student_bulk_upload.xlsx",
        as_attachment=True
    )


@student_master_bp.route("/upload/basic-bulk-excel", methods=["GET", "POST"])
def upload_basic_bulk_excel():
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        file = request.files["file"]
        path = "static/uploads/temp_student_bulk.xlsx"
        file.save(path)

        process_basic_student_excel(path)
        flash("Students uploaded successfully (Excel)", "success")
        return redirect(url_for("student_master.student_list"))

    return render_template("student_master/basic_bulk_excel_upload.html")


# --------------------------------------------------
# MASTER BIODATA
# --------------------------------------------------
@student_master_bp.route("/master-biodata", methods=["GET", "POST"])
def master_biodata():
    if not superintendent_only():
        return redirect(url_for("dashboard.dashboard"))

    ledger = request.args.get("ledger_no")
    data = get_student_full_by_ledger(ledger) if ledger else None

    if request.method == "POST":
        ledger = request.form["ledger_no"]
        try:
            if not data:
                db = get_db()
                cur = db.cursor()
                cur.execute("""
                    INSERT INTO students
                    (ledger_no, student_name, class, section, status)
                    VALUES (?, ?, ?, ?, 'ACTIVE')
                """, (
                    ledger,
                    request.form["student_name"],
                    request.form["class"],
                    request.form.get("section")
                ))
                db.commit()
                db.close()
                data = get_student_full_by_ledger(ledger)

            save_biodata(
                data["student"]["id"],
                ledger,
                request.form,
                request.files
            )
        except Exception as exc:
            flash(f"Unable to save biodata: {exc}", "danger")
            return redirect(url_for("student_master.master_biodata", ledger_no=ledger))

        flash("Biodata saved successfully", "success")
        return redirect(url_for("student_master.master_biodata", ledger_no=ledger))

    return render_template(
        "student_master/biodata_master.html",
        data=data,
        ledger=ledger
    )


# --------------------------------------------------
# STUDENT REGISTRY
# --------------------------------------------------
@student_master_bp.route("/list")
def student_list():
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "ACTIVE")
    page = max(int(request.args.get("page", 1) or 1), 1)
    per_page = 20

    db = get_db()
    cur = db.cursor()

    base_query = """
        FROM students s
        LEFT JOIN student_biodata sb ON sb.student_id = s.id
        WHERE 1=1
    """
    filter_params = []

    if status:
        base_query += " AND s.status = ? "
        filter_params.append(status)

    if q:
        base_query += """
        AND (
            s.ledger_no LIKE ?
            OR s.student_name LIKE ?
            OR s.class LIKE ?
        )
        """
        filter_params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    cur.execute(f"SELECT COUNT(*) {base_query}", filter_params)
    total_students = cur.fetchone()[0]
    total_pages = max((total_students + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    query = """
        SELECT s.ledger_no, s.student_name, s.class, s.section,
               s.biodata_completed, s.status, sb.student_photo
    """ + base_query + """
        ORDER BY s.class, s.section, s.student_name
        LIMIT ? OFFSET ?
    """
    params = list(filter_params)
    params.extend([per_page, offset])

    cur.execute(query, params)
    students = cur.fetchall()
    db.close()

    return render_template(
        "student_master/student_list.html",
        students=students,
        q=q,
        status=status,
        page=page,
        per_page=per_page,
        total_students=total_students,
        total_pages=total_pages
    )


@student_master_bp.route("/delete/<ledger_no>", methods=["POST"])
def delete_student(ledger_no):
    if not superintendent_only():
        return redirect(url_for("dashboard.dashboard"))

    try:
        delete_student_record(ledger_no)
        flash(f"Student {ledger_no} deleted successfully", "success")
    except Exception as exc:
        flash(str(exc), "danger")

    return redirect(url_for("student_master.student_list"))


# --------------------------------------------------
# BIODATA EXCEL (FULL)
# --------------------------------------------------
@student_master_bp.route("/download/biodata-excel")
def download_biodata_excel():
    wb = generate_full_biodata_excel()
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        download_name="student_biodata.xlsx",
        as_attachment=True
    )


@student_master_bp.route("/upload/biodata-excel", methods=["GET", "POST"])
def upload_biodata_excel():
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        file = request.files["file"]
        path = "static/uploads/temp_biodata.xlsx"
        file.save(path)
        process_biodata_excel(path)
        flash("Excel biodata uploaded successfully", "success")
        return redirect(url_for("student_master.intake_dashboard"))

    return render_template("student_master/biodata_excel_upload.html")


# --------------------------------------------------
# STUDENT STATUS CHANGE (FINAL)
# --------------------------------------------------
@student_master_bp.route("/status/<ledger_no>", methods=["GET", "POST"])
def student_status_change(ledger_no):
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT ledger_no, student_name, status
        FROM students
        WHERE ledger_no = ?
    """, (ledger_no,))
    student = cur.fetchone()
    db.close()

    if not student:
        flash("Student not found", "danger")
        return redirect(url_for("student_master.student_list"))

    if request.method == "POST":
        new_status = request.form.get("status")
        reason = request.form.get("reason")

        change_student_status(ledger_no, new_status, reason)
        flash(f"Student status updated to {new_status}", "success")

        return redirect(url_for("student_master.student_list"))

    return render_template(
        "student_master/student_status_change.html",
        student=student
    )


# --------------------------------------------------
# STUDENT PROFILE – 360° VIEW
# --------------------------------------------------
@student_master_bp.route("/profile/<ledger_no>")
def student_profile(ledger_no):
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    data = get_student_full_by_ledger(ledger_no)
    if not data:
        flash("Student not found", "danger")
        return redirect(url_for("student_master.student_list"))

    student = data["student"]
    current_bed, bed_history = get_student_bed_info(ledger_no)
    self_going, devices = get_student_permissions(student["id"])

    return render_template(
        "student_master/student_profile.html",
        data=data,
        current_bed=current_bed,
        bed_history=bed_history,
        self_going=self_going,
        devices=devices
    )


# --------------------------------------------------
# SYSTEM VERIFICATION SCREEN
# --------------------------------------------------
@student_master_bp.route("/verify/<ledger_no>")
def system_verify_student(ledger_no):
    if not superintendent_only():
        return redirect(url_for("dashboard"))

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT ledger_no, student_name, class, section, status
        FROM students
        WHERE ledger_no = ?
    """, (ledger_no,))
    student = cur.fetchone()

    if not student:
        db.close()
        flash("Student not found", "danger")
        return redirect(url_for("student_master.student_list"))

    cur.execute("""
        SELECT b.block_name, b.room_number, b.bed_number,
               a.status, a.vacate_reason
        FROM bed_allotments a
        JOIN beds_master b ON a.bed_id = b.id
        WHERE a.ledger_number = ?
        ORDER BY a.created_at DESC
        LIMIT 1
    """, (ledger_no,))
    bed = cur.fetchone()

    cur.execute("""
        SELECT allowed, revoked_reason
        FROM student_self_going
        WHERE student_id = (
            SELECT id FROM students WHERE ledger_no = ?
        )
        ORDER BY created_at DESC
        LIMIT 1
    """, (ledger_no,))
    self_going = cur.fetchone()

    cur.execute("""
        SELECT device_type, allowed, revoked_reason
        FROM student_device_permission
        WHERE student_id = (
            SELECT id FROM students WHERE ledger_no = ?
        )
        ORDER BY created_at DESC
        LIMIT 1
    """, (ledger_no,))
    device = cur.fetchone()

    db.close()

    return render_template(
        "student_master/system_verify.html",
        student=student,
        bed=bed,
        self_going=self_going,
        device=device
    )
