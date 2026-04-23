from models.db import get_db


def get_all_sessions():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM academic_sessions
        WHERE is_deleted = 0
        ORDER BY start_date DESC
    """)
    rows = cur.fetchall()
    db.close()
    return rows


def get_active_session():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM academic_sessions
        WHERE is_active = 1 AND is_deleted = 0
        LIMIT 1
    """)
    row = cur.fetchone()
    db.close()
    return row


def create_session(name, start_date, end_date):
    db = get_db()
    cur = db.cursor()

    # Deactivate all sessions
    cur.execute("""
        UPDATE academic_sessions
        SET is_active = 0
    """)

    # Insert new active session
    cur.execute("""
        INSERT INTO academic_sessions
        (name, start_date, end_date, is_active, is_deleted)
        VALUES (?, ?, ?, 1, 0)
    """, (name, start_date, end_date))

    db.commit()
    db.close()


def can_delete_session(session_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT is_active
        FROM academic_sessions
        WHERE id = ? AND is_deleted = 0
    """, (session_id,))
    row = cur.fetchone()
    db.close()

    if not row:
        return False, "Session not found"

    if row["is_active"] == 1:
        return False, "Active session cannot be deleted"

    # Future child-table checks go here
    # student_sessions, hostel_allotments, fees, attendance etc.

    return True, ""


def soft_delete_session(session_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE academic_sessions
        SET is_deleted = 1,
            is_active = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (session_id,))

    db.commit()
    db.close()
