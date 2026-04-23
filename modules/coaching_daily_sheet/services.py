from datetime import datetime
from models.db import get_db
from .models import init_tables

DAY_MAP = {
    0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"
}

def get_day_name_from_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return DAY_MAP[dt.weekday()]


# ==========================================================
# DAILY SHEET (AUTO GENERATION)
# ==========================================================
def ensure_daily_sheet(date_str, created_by="SYSTEM"):
    init_tables()
    day_name = get_day_name_from_date(date_str)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM coaching_daily_sheet WHERE sheet_date=?", (date_str,))
    coaching_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM study_duty_daily_sheet WHERE sheet_date=?", (date_str,))
    study_count = cur.fetchone()[0]

    if coaching_count == 0:
        cur.execute("""
            SELECT day_name, class_name, subject, start_time, end_time, teacher_name
            FROM coaching_weekly_master
            WHERE day_name=? AND status='ACTIVE'
            ORDER BY id ASC
        """, (day_name,))
        rows = cur.fetchall()

        for r in rows:
            cur.execute("""
                INSERT INTO coaching_daily_sheet
                (sheet_date, day_name, class_name, subject, start_time, end_time, teacher_name, status, remark, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', '', ?)
            """, (date_str, day_name, r["class_name"], r["subject"], r["start_time"], r["end_time"], r["teacher_name"], created_by))

    if study_count == 0:
        cur.execute("""
            SELECT day_name, class_group, floor_place, teacher_name, start_time, end_time
            FROM study_duty_weekly_master
            WHERE day_name=? AND status='ACTIVE'
            ORDER BY id ASC
        """, (day_name,))
        rows = cur.fetchall()

        for r in rows:
            cur.execute("""
                INSERT INTO study_duty_daily_sheet
                (sheet_date, day_name, class_group, floor_place, teacher_name, start_time, end_time, status, remark, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', '', ?)
            """, (date_str, day_name, r["class_group"], r["floor_place"], r["teacher_name"], r["start_time"], r["end_time"], created_by))

    conn.commit()
    conn.close()
    return day_name


def get_daily_coaching_rows(date_str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM coaching_daily_sheet WHERE sheet_date=? ORDER BY id ASC", (date_str,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_daily_study_rows(date_str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM study_duty_daily_sheet WHERE sheet_date=? ORDER BY id ASC", (date_str,))
    rows = cur.fetchall()
    conn.close()
    return rows


def update_coaching_row(row_id, form, updated_by="ADMIN"):
    status = form.get("status", "ACTIVE")
    remark = (form.get("remark") or "").strip()

    if status != "ACTIVE" and remark == "":
        return False, "❌ Remark is mandatory if routine is suspended/changed."

    subject = form.get("subject", "")
    start_time = form.get("start_time", "")
    end_time = form.get("end_time", "")
    teacher_name = form.get("teacher_name", "")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE coaching_daily_sheet
        SET subject=?, start_time=?, end_time=?, teacher_name=?, status=?, remark=?, updated_by=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (subject, start_time, end_time, teacher_name, status, remark, updated_by, row_id))

    conn.commit()
    conn.close()
    return True, "✅ Coaching row updated"


def update_study_row(row_id, form, updated_by="ADMIN"):
    status = form.get("status", "ACTIVE")
    remark = (form.get("remark") or "").strip()

    if status != "ACTIVE" and remark == "":
        return False, "❌ Remark is mandatory if duty is suspended/changed."

    floor_place = form.get("floor_place", "")
    teacher_name = form.get("teacher_name", "")
    start_time = form.get("start_time", "")
    end_time = form.get("end_time", "")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE study_duty_daily_sheet
        SET floor_place=?, teacher_name=?, start_time=?, end_time=?, status=?, remark=?, updated_by=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (floor_place, teacher_name, start_time, end_time, status, remark, updated_by, row_id))

    conn.commit()
    conn.close()
    return True, "✅ Study duty row updated"


# ==========================================================
# MASTER ROUTINE (WEEKLY MASTER EDITING)
# ==========================================================
def get_coaching_weekly_master(day_name=None):
    conn = get_db()
    cur = conn.cursor()

    if day_name:
        cur.execute("""
            SELECT * FROM coaching_weekly_master
            WHERE day_name=?
            ORDER BY id ASC
        """, (day_name,))
    else:
        cur.execute("""
            SELECT * FROM coaching_weekly_master
            ORDER BY day_name ASC, id ASC
        """)

    rows = cur.fetchall()
    conn.close()
    return rows


def get_study_weekly_master(day_name=None):
    conn = get_db()
    cur = conn.cursor()

    if day_name:
        cur.execute("""
            SELECT * FROM study_duty_weekly_master
            WHERE day_name=?
            ORDER BY id ASC
        """, (day_name,))
    else:
        cur.execute("""
            SELECT * FROM study_duty_weekly_master
            ORDER BY day_name ASC, id ASC
        """)

    rows = cur.fetchall()
    conn.close()
    return rows


def update_weekly_coaching_row(row_id, form, updated_by="ADMIN"):
    subject = (form.get("subject") or "").strip()
    teacher_name = (form.get("teacher_name") or "").strip()
    start_time = (form.get("start_time") or "").strip()
    end_time = (form.get("end_time") or "").strip()
    status = form.get("status", "ACTIVE")

    if subject == "" or start_time == "" or end_time == "":
        return False, "❌ Subject, Start Time, End Time cannot be empty."

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE coaching_weekly_master
        SET subject=?, teacher_name=?, start_time=?, end_time=?, status=?
        WHERE id=?
    """, (subject, teacher_name, start_time, end_time, status, row_id))

    conn.commit()
    conn.close()
    return True, "✅ Weekly Coaching Master updated"


def update_weekly_study_row(row_id, form, updated_by="ADMIN"):
    class_group = (form.get("class_group") or "").strip()
    floor_place = (form.get("floor_place") or "").strip()
    teacher_name = (form.get("teacher_name") or "").strip()
    start_time = (form.get("start_time") or "").strip()
    end_time = (form.get("end_time") or "").strip()
    status = form.get("status", "ACTIVE")

    if class_group == "" or floor_place == "" or start_time == "" or end_time == "":
        return False, "❌ Class group, place, start/end time cannot be empty."

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE study_duty_weekly_master
        SET class_group=?, floor_place=?, teacher_name=?, start_time=?, end_time=?, status=?
        WHERE id=?
    """, (class_group, floor_place, teacher_name, start_time, end_time, status, row_id))

    conn.commit()
    conn.close()
    return True, "✅ Weekly Self Study Master updated"


def bulk_suspend_weekly(day_name, routine_type, reason, updated_by="ADMIN"):
    """
    routine_type = 'COACHING' or 'STUDY'
    """
    reason = (reason or "").strip()
    if reason == "":
        return False, "❌ Suspension reason is mandatory."

    conn = get_db()
    cur = conn.cursor()

    if routine_type == "COACHING":
        cur.execute("""
            UPDATE coaching_weekly_master
            SET status='SUSPENDED', teacher_name=teacher_name
            WHERE day_name=?
        """, (day_name,))
    else:
        cur.execute("""
            UPDATE study_duty_weekly_master
            SET status='SUSPENDED'
            WHERE day_name=?
        """, (day_name,))

    conn.commit()
    conn.close()

    return True, f"✅ {routine_type} weekly master suspended for {day_name}. Reason: {reason}"
