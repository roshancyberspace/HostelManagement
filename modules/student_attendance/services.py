import json
import os
import base64
from datetime import datetime, date
from flask import current_app
from models.db import get_db


# ==================================================
# ATTENDANCE SLOT DEFINITIONS
# ==================================================

WORKING_SLOTS = [
    "MORNING",              # Breakfast / School Reporting
    "AFTERNOON_RETURN",     # School Dispersal / Hostel Reporting Back
    "COACHING",             # Afternoon Coaching
    "EVENING",              # Assembly / Sports
    "NIGHT"                 # Dinner / Final Roll Call
]

HOLIDAY_SLOTS = [
    "MORNING",              # Breakfast
    "EVENING",              # Assembly / Sports
    "NIGHT"                 # Dinner
]


def get_active_classes():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT class
        FROM students
        WHERE status = 'ACTIVE'
          AND class IS NOT NULL
          AND TRIM(class) <> ''
        ORDER BY class
    """)
    rows = [row["class"] for row in cur.fetchall()]
    conn.close()
    return rows


# ==================================================
# DAY TYPE LOGIC
# ==================================================

def get_day_type(att_date: date):
    """
    Sunday = HOLIDAY
    All other days = WORKING
    """
    return "HOLIDAY" if att_date.weekday() == 6 else "WORKING"


def get_slots_for_day(att_date: date):
    return HOLIDAY_SLOTS if get_day_type(att_date) == "HOLIDAY" else WORKING_SLOTS


# ==================================================
# GATEPASS CHECK (READ-ONLY, FROZEN SAFE)
# ==================================================

def has_active_gatepass(ledger_no):
    """
    Gatepass logic:
    student_self_going.allowed = 1
    means student is OUTSIDE campus.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(student_self_going)")
    gatepass_columns = {row["name"] for row in cur.fetchall()}

    if "ledger_no" in gatepass_columns:
        cur.execute("""
            SELECT 1
            FROM student_self_going
            WHERE ledger_no = ?
              AND allowed = 1
            LIMIT 1
        """, (ledger_no,))
    elif "student_id" in gatepass_columns:
        cur.execute("""
            SELECT 1
            FROM student_self_going ssg
            JOIN students s ON s.id = ssg.student_id
            WHERE s.ledger_no = ?
              AND ssg.allowed = 1
              AND COALESCE(ssg.is_active, 1) = 1
            LIMIT 1
        """, (ledger_no,))
    else:
        conn.close()
        return False

    row = cur.fetchone()
    conn.close()

    return row is not None


# ==================================================
# FETCH ACTIVE STUDENTS (CLASS-AWARE)
# ==================================================

def fetch_active_students(filters=None):
    """
    Fetch ACTIVE students only.
    Uses actual schema:
    - students.class
    - students.student_name
    """
    conn = get_db()
    cur = conn.cursor()

    sql = """
        SELECT s.*, sb.student_photo
        FROM students s
        LEFT JOIN student_biodata sb ON sb.student_id = s.id
        WHERE s.status = 'ACTIVE'
    """
    params = []

    if filters and filters.get("class"):
        sql += " AND class = ?"
        params.append(filters["class"])

    sql += " ORDER BY class, student_name"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return rows


def save_attendance_face(data_url, ledger_no, att_date, slot):
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

    base_folder = os.path.join(current_app.instance_path, "attendance_faces")
    os.makedirs(base_folder, exist_ok=True)
    filename = f"{ledger_no}_{att_date.isoformat()}_{slot}_{datetime.now().strftime('%H%M%S')}.{ext}"
    path = os.path.join(base_folder, filename)
    with open(path, "wb") as image_file:
        image_file.write(raw)
    return f"instance_uploads/attendance_faces/{filename}"


def get_attendance_status_totals(att_date, slot):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT status, COUNT(*) AS total
        FROM student_attendance
        WHERE attendance_date = ?
          AND slot = ?
        GROUP BY status
    """, (att_date.isoformat(), slot))
    rows = {row["status"]: row["total"] for row in cur.fetchall()}
    conn.close()
    return {
        "PRESENT": rows.get("PRESENT", 0),
        "ABSENT": rows.get("ABSENT", 0),
        "LEAVE": rows.get("LEAVE", 0),
        "MEDICAL": rows.get("MEDICAL", 0),
    }


# ==================================================
# BED / HOSTEL SNAPSHOT (READ-ONLY)
# ==================================================

def get_bed_snapshot(ledger_no):
    """
    Captures current hostel location of student.
    Snapshot is stored for audit history.
    """
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                h.name AS hostel,
                b.name AS block,
                COALESCE(f.name, f.floor_name) AS floor,
                r.room_no AS room,
                bd.bed_no AS bed
            FROM bed_allotment ba
            JOIN beds bd ON ba.bed_id = bd.id
            JOIN rooms r ON bd.room_id = r.id
            JOIN floors f ON r.floor_id = f.id
            LEFT JOIN blocks b ON f.block_id = b.id
            LEFT JOIN hostels h ON b.hostel_id = h.id
            WHERE ba.ledger_no = ?
              AND COALESCE(ba.is_active, 1) = 1
            LIMIT 1
        """, (ledger_no,))
    except Exception:
        conn.close()
        return {}

    row = cur.fetchone()
    conn.close()

    if not row:
        return {}

    return dict(row)


# ==================================================
# MARK ATTENDANCE (CORE ENGINE)
# ==================================================

def mark_attendance(
    ledger_no,
    att_date,
    slot,
    status,
    marked_by,
    remarks=None,
    application_file=None,
    captured_photo_data=None
):
    """
    Core attendance engine.

    RULES ENFORCED:
    - Gatepass => ABSENT (outside campus)
    - Others always inside campus
    - No delete, no overwrite
    - Snapshot preserved
    """

    conn = get_db()
    cur = conn.cursor()

    gatepass_active = has_active_gatepass(ledger_no)
    final_status = "ABSENT" if gatepass_active else status

    snapshot = get_bed_snapshot(ledger_no)
    saved_face_path = save_attendance_face(captured_photo_data, ledger_no, att_date, slot)
    stored_application_file = saved_face_path or application_file
    if saved_face_path:
        snapshot["face_evidence"] = saved_face_path

    cur.execute("""
        INSERT INTO student_attendance (
            ledger_no,
            attendance_date,
            day_type,
            slot,
            status,
            remarks,
            application_file,
            is_gatepass,
            snapshot,
            marked_by,
            marked_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ledger_no, attendance_date, slot) DO UPDATE SET
            day_type = excluded.day_type,
            status = excluded.status,
            remarks = excluded.remarks,
            application_file = excluded.application_file,
            is_gatepass = excluded.is_gatepass,
            snapshot = excluded.snapshot,
            marked_by = excluded.marked_by,
            marked_at = excluded.marked_at,
            corrected = 1
    """, (
        ledger_no,
        att_date.isoformat(),
        get_day_type(att_date),
        slot,
        final_status,
        remarks,
        stored_application_file,
        1 if gatepass_active else 0,
        json.dumps(snapshot),
        marked_by,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


# ==================================================
# ABSENT LIST (FOR DASHBOARD & REPORTS)
# ==================================================

def get_absent_students(att_date, slot):
    """
    Returns all ABSENT students for a slot.
    Used by superintendent dashboard & reports.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sa.*,
            s.student_name,
            s.class
        FROM student_attendance sa
        LEFT JOIN students s ON sa.ledger_no = s.ledger_no
        WHERE sa.attendance_date = ?
          AND sa.slot = ?
          AND sa.status = 'ABSENT'
        ORDER BY s.class, s.student_name
    """, (att_date.isoformat(), slot))

    rows = cur.fetchall()
    conn.close()

    return rows
# ==================================================
# DASHBOARD SUMMARY (CLASS + BLOCK)
# ==================================================

def get_slot_summary(att_date, slot):
    """
    Returns counts grouped by class + block.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE(s.class, json_extract(sa.snapshot, '$.class'), 'Unassigned') AS class,
            COALESCE(json_extract(sa.snapshot, '$.block'), 'Unassigned') AS block,
            sa.status,
            COUNT(*) as total
        FROM student_attendance sa
        LEFT JOIN students s ON sa.ledger_no = s.ledger_no
        WHERE sa.attendance_date = ?
          AND sa.slot = ?
        GROUP BY class, block, sa.status
        ORDER BY class, block, sa.status
    """, (att_date.isoformat(), slot))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_strength_count(att_date, slot):
    """
    Total strength for a slot (excluding gatepass absentees).
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) as total
        FROM student_attendance
        WHERE attendance_date = ?
          AND slot = ?
          AND is_gatepass = 0
    """, (att_date.isoformat(), slot))

    total = cur.fetchone()["total"]
    conn.close()
    return total

# ==================================================
# MANAGEMENT DAILY REPORT (CLASS + BLOCK)
# ==================================================

def get_daily_management_report(att_date):
    """
    Returns slot-wise counts grouped by Class + Block.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE(s.class, json_extract(sa.snapshot, '$.class'), 'Unassigned') AS class,
            COALESCE(json_extract(sa.snapshot, '$.block'), 'Unassigned') AS block,
            sa.slot,
            sa.status,
            COUNT(*) AS total
        FROM student_attendance sa
        LEFT JOIN students s ON sa.ledger_no = s.ledger_no
        WHERE sa.attendance_date = ?
        GROUP BY class, block, sa.slot, sa.status
        ORDER BY class, block, sa.slot, sa.status
    """, (att_date.isoformat(),))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_slot_total(att_date, slot):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM student_attendance
        WHERE attendance_date = ?
          AND slot = ?
          AND is_gatepass = 0
    """, (att_date.isoformat(), slot))

    total = cur.fetchone()["total"]
    conn.close()
    return total
