from models.db import get_db


DAYS = [
    ("MONDAY", "सोमवार"),
    ("TUESDAY", "मंगलवार"),
    ("WEDNESDAY", "बुधवार"),
    ("THURSDAY", "गुरुवार"),
    ("FRIDAY", "शुक्रवार"),
    ("SATURDAY", "शनिवार"),
]


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


def get_active_laundry_routine():
    session = get_active_session()
    if not session:
        return None, []

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT * FROM laundry_weekly_routine
        WHERE session_id = ? AND is_active = 1
        LIMIT 1
    """, (session["id"],))

    header = cur.fetchone()

    if not header:
        db.close()
        return None, []

    cur.execute("""
        SELECT * FROM laundry_routine_items
        WHERE routine_id = ?
        ORDER BY id
    """, (header["id"],))

    rows = cur.fetchall()
    db.close()
    return header, rows


def create_laundry_routine(title):
    session = get_active_session()
    if not session:
        raise Exception("No active session")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE laundry_weekly_routine
        SET is_active = 0
        WHERE session_id = ?
    """, (session["id"],))

    cur.execute("""
        INSERT INTO laundry_weekly_routine (session_id, title)
        VALUES (?, ?)
    """, (session["id"], title))

    routine_id = cur.lastrowid

    for d, _ in DAYS:
        cur.execute("""
            INSERT INTO laundry_routine_items
            (routine_id, day_name)
            VALUES (?, ?)
        """, (routine_id, d))

    db.commit()
    db.close()


def save_laundry_routine(routine_id, form):
    db = get_db()
    cur = db.cursor()

    for d, _ in DAYS:
        cur.execute("""
            UPDATE laundry_routine_items
            SET deposit = ?, deliver = ?
            WHERE routine_id = ? AND day_name = ?
        """, (
            form.get(f"{d}_deposit"),
            form.get(f"{d}_deliver"),
            routine_id,
            d
        ))

    db.commit()
    db.close()
