import os
from datetime import datetime
from werkzeug.utils import secure_filename

from models.db import get_db
from .models import init_laundry_register_table


UPLOAD_FOLDER = "static/uploads/laundry"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _ensure_tables():
    init_laundry_register_table()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_laundry_photo(file, ledger_no, stage):
    if not file or not file.filename:
        return ""
    if not allowed_file(file.filename):
        raise Exception("Laundry photo must be JPG, JPEG, PNG, or WEBP.")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[1].lower()
    safe_name = secure_filename(
        f"{ledger_no}_{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    )
    path = os.path.join(UPLOAD_FOLDER, safe_name).replace("\\", "/")
    file.save(path)
    return path


# ---------- COMMON ----------
def get_active_session():
    _ensure_tables()
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT * FROM academic_sessions
        WHERE is_active = 1 AND is_deleted = 0
        LIMIT 1
    """)
    row = cur.fetchone()
    db.close()
    return row


# ---------- STUDENT LOOKUP ----------
def get_student_by_ledger(ledger_no):
    _ensure_tables()
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT s.ledger_no, s.student_name, s.class, s.section, sb.student_photo
        FROM students s
        LEFT JOIN student_biodata sb ON sb.student_id = s.id
        WHERE ledger_no = ? AND is_active = 1
    """, (ledger_no,))

    row = cur.fetchone()
    db.close()

    if not row:
        return None

    return {
        "ledger_no": row["ledger_no"],
        "student_name": row["student_name"],
        "class_section": f"{row['class']}-{row['section'] or '-'}",
        "student_photo": row["student_photo"] or ""
    }


# ---------- REGISTER ----------
def get_all_records():
    _ensure_tables()
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT * FROM laundry_register
        ORDER BY date_given DESC, id DESC
    """)
    rows = cur.fetchall()
    db.close()
    return rows


def issue_laundry(form, files):
    session = get_active_session()
    if not session:
        raise Exception("No active academic session")

    ledger_no = form.get("ledger_no")
    student = get_student_by_ledger(ledger_no)

    if not student:
        raise Exception("Ledger number not found")

    issue_photo_path = save_laundry_photo(files.get("issue_photo"), student["ledger_no"], "issue")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO laundry_register
        (session_id, ledger_no, student_name, class_section,
         items_given, date_given, status, issue_photo_path)
        VALUES (?, ?, ?, ?, ?, DATE('now'), 'GIVEN', ?)
    """, (
        session["id"],
        student["ledger_no"],
        student["student_name"],
        student["class_section"],
        form.get("items_given"),
        issue_photo_path
    ))

    db.commit()
    db.close()


def mark_return(record_id, form, files):
    _ensure_tables()
    db = get_db()
    cur = db.cursor()
    return_photo_path = save_laundry_photo(files.get("return_photo"), f"record_{record_id}", "return")

    cur.execute("""
        UPDATE laundry_register
        SET items_returned = ?,
            date_returned = DATE('now'),
            status = 'RETURNED',
            remarks = ?,
            return_photo_path = CASE
                WHEN ? <> '' THEN ?
                ELSE return_photo_path
            END
        WHERE id = ?
    """, (
        form.get("items_returned"),
        form.get("remarks"),
        return_photo_path,
        return_photo_path,
        record_id
    ))

    db.commit()
    db.close()
