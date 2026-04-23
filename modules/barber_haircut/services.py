import base64
import os
from datetime import datetime

from flask import current_app
from werkzeug.utils import secure_filename

from models.db import get_db
from .models import init_barber_tables


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_data_url_photo(data_url, ledger_no, month_key, stage):
    if not data_url or "," not in data_url:
        return ""

    try:
        header, encoded = data_url.split(",", 1)
        ext = "jpg"
        if "image/png" in header:
            ext = "png"
        elif "image/webp" in header:
            ext = "webp"
        raw = base64.b64decode(encoded)
    except Exception:
        return ""

    upload_folder = os.path.join(current_app.instance_path, "haircuts")
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(
        f"{ledger_no}_{month_key}_{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    )
    path = os.path.join(upload_folder, filename)
    with open(path, "wb") as image_file:
        image_file.write(raw)
    return f"instance_uploads/haircuts/{filename}"


def get_current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def _ensure_tables():
    init_barber_tables()


def fetch_student_by_ledger(ledger_no: str):
    _ensure_tables()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            s.ledger_no,
            s.student_name,
            COALESCE(p.class, '') AS class_name,
            COALESCE(p.section, '') AS section,
            s.status
        FROM students s
        LEFT JOIN student_profile p ON p.ledger_no = s.ledger_no
        WHERE s.ledger_no = ?
    """, (ledger_no,))
    row = cur.fetchone()
    conn.close()
    return row


def create_haircut_record(form, before_file, after_file):
    _ensure_tables()

    ledger_no = (form.get("ledger_no") or "").strip()
    haircut_date = (form.get("haircut_date") or "").strip()
    barber_name = (form.get("barber_name") or "").strip()
    remark = (form.get("remark") or "").strip()

    if not ledger_no or not haircut_date:
        return False, "Ledger number and haircut date are required."

    student = fetch_student_by_ledger(ledger_no)
    if not student:
        return False, "Student was not found for the provided ledger number."

    if student["status"] != "ACTIVE":
        return False, "Haircut entry is allowed only for active students."

    month_key = haircut_date[:7]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM barber_haircut_records
        WHERE ledger_no = ? AND haircut_month = ?
    """, (ledger_no, month_key))
    already = cur.fetchone()[0]
    conn.close()

    if already > 0:
        return False, f"Haircut is already recorded for {month_key}."

    upload_folder = os.path.join(current_app.instance_path, "haircuts")
    os.makedirs(upload_folder, exist_ok=True)

    before_path = save_data_url_photo(
        form.get("captured_before_photo"),
        ledger_no,
        month_key,
        "BEFORE"
    )
    after_path = save_data_url_photo(
        form.get("captured_after_photo"),
        ledger_no,
        month_key,
        "AFTER"
    )

    if not before_path and before_file and before_file.filename:
        if not allowed_file(before_file.filename):
            return False, "Before photo must be JPG, JPEG, PNG, or WEBP."
        filename = secure_filename(before_file.filename)
        before_name = f"{ledger_no}_{month_key}_BEFORE_{filename}"
        before_file.save(os.path.join(upload_folder, before_name))
        before_path = f"instance_uploads/haircuts/{before_name}"

    if not after_path and after_file and after_file.filename:
        if not allowed_file(after_file.filename):
            return False, "After photo must be JPG, JPEG, PNG, or WEBP."
        filename = secure_filename(after_file.filename)
        after_name = f"{ledger_no}_{month_key}_AFTER_{filename}"
        after_file.save(os.path.join(upload_folder, after_name))
        after_path = f"instance_uploads/haircuts/{after_name}"

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO barber_haircut_records
        (ledger_no, student_name, class_name, section, haircut_month, haircut_date,
         barber_name, before_photo_path, after_photo_path, remark, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DONE')
    """, (
        student["ledger_no"],
        student["student_name"],
        student["class_name"],
        student["section"],
        month_key,
        haircut_date,
        barber_name,
        before_path,
        after_path,
        remark
    ))
    conn.commit()
    conn.close()

    return True, "Haircut record saved successfully."


def get_monthly_done_list(month_key=None):
    _ensure_tables()
    if not month_key:
        month_key = get_current_month()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM barber_haircut_records
        WHERE haircut_month = ?
        ORDER BY haircut_date DESC
    """, (month_key,))
    rows = cur.fetchall()
    conn.close()
    return rows, month_key


def get_defaulter_list(month_key=None, cutoff_day=15):
    _ensure_tables()
    if not month_key:
        month_key = get_current_month()

    today_day = int(datetime.now().strftime("%d"))
    cutoff_active = today_day > cutoff_day
    if not cutoff_active:
        return [], month_key, cutoff_active, cutoff_day

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            s.ledger_no,
            s.student_name,
            COALESCE(p.class, '') AS class_name,
            COALESCE(p.section, '') AS section
        FROM students s
        LEFT JOIN student_profile p ON p.ledger_no = s.ledger_no
        WHERE s.status = 'ACTIVE'
          AND s.ledger_no NOT IN (
              SELECT ledger_no
              FROM barber_haircut_records
              WHERE haircut_month = ?
          )
        ORDER BY class_name ASC, section ASC, s.student_name ASC
    """, (month_key,))
    rows = cur.fetchall()
    conn.close()
    return rows, month_key, cutoff_active, cutoff_day


def get_student_history(ledger_no: str):
    _ensure_tables()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM barber_haircut_records
        WHERE ledger_no = ?
        ORDER BY haircut_date DESC
    """, (ledger_no,))
    rows = cur.fetchall()
    conn.close()
    return rows
