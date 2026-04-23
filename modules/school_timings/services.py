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


def get_all_timings():
    session = get_active_session()
    if not session:
        return []

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM school_timings
        WHERE session_id = ? AND is_deleted = 0
        ORDER BY day_type
    """, (session["id"],))
    rows = cur.fetchall()
    db.close()
    return rows


def create_timing(day_type, reporting, recess, dispersal_senior, dispersal_junior):
    session = get_active_session()
    if not session:
        raise Exception("No active academic session")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO school_timings
        (session_id, day_type, reporting_time, recess_time,
         dispersal_senior, dispersal_junior)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session["id"],
        day_type,
        reporting,
        recess,
        dispersal_senior,
        dispersal_junior
    ))

    db.commit()
    db.close()


def can_delete_timing(timing_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id FROM school_timings
        WHERE id = ? AND is_deleted = 0
    """, (timing_id,))
    row = cur.fetchone()
    db.close()

    if not row:
        return False, "Timing not found"

    # Future child checks: hostel timetable
    return True, ""


def soft_delete_timing(timing_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE school_timings
        SET is_deleted = 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (timing_id,))

    db.commit()
    db.close()
