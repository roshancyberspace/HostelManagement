from models.db import get_db


def get_active_session():
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


def get_school_timing(day_type):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT * FROM school_timings
        WHERE day_type = ? AND is_deleted = 0
        ORDER BY id DESC LIMIT 1
    """, (day_type,))
    row = cur.fetchone()
    db.close()
    return row


def get_timetable(day_type):
    session = get_active_session()
    if not session:
        return []

    school = get_school_timing(day_type)

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM hostel_timetable
        WHERE session_id = ?
          AND day_type = ?
          AND is_deleted = 0
        ORDER BY sequence_no
    """, (session["id"], day_type))
    rows = cur.fetchall()
    db.close()

    resolved = []
    for r in rows:
        start = r["start_time"]
        end = r["end_time"]

        if r["time_source"] == "SCHOOL_REPORTING" and school:
            start = school["reporting_time"]
        elif r["time_source"] == "SCHOOL_RECESS" and school:
            start = school["recess_time"]
        elif r["time_source"] == "SCHOOL_LUNCH" and school:
            start = school["dispersal_junior"]

        resolved.append({**r, "resolved_start": start, "resolved_end": end})

    return resolved


def add_activity(day_type, name, start, end, source, seq):
    session = get_active_session()
    if not session:
        raise Exception("No active session")

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO hostel_timetable
        (session_id, day_type, activity_name, start_time, end_time, time_source, sequence_no)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session["id"], day_type, name, start, end, source, seq))
    db.commit()
    db.close()


def update_activity(row_id, start, end, seq):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE hostel_timetable
        SET start_time = ?, end_time = ?, sequence_no = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (start, end, seq, row_id))
    db.commit()
    db.close()


def soft_delete_activity(row_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE hostel_timetable
        SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (row_id,))
    db.commit()
    db.close()
