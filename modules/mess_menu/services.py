from datetime import datetime

from models.db import get_db


DAYS = [
    ("MONDAY", "Monday"),
    ("TUESDAY", "Tuesday"),
    ("WEDNESDAY", "Wednesday"),
    ("THURSDAY", "Thursday"),
    ("FRIDAY", "Friday"),
    ("SATURDAY", "Saturday"),
    ("SUNDAY", "Sunday"),
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


def get_active_weekly_menu(day_type):
    session = get_active_session()
    if not session:
        return None, []

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT * FROM mess_menu_weekly
        WHERE session_id = ?
          AND day_type = ?
          AND is_active = 1
        ORDER BY id DESC
        LIMIT 1
    """, (session["id"], day_type))

    header = cur.fetchone()

    if not header:
        db.close()
        return None, []

    cur.execute("""
        SELECT * FROM mess_menu_items
        WHERE weekly_menu_id = ?
        ORDER BY id
    """, (header["id"],))

    items = cur.fetchall()
    db.close()
    return header, items


def create_new_weekly_menu(day_type, title):
    session = get_active_session()
    if not session:
        raise Exception("No active session")

    title = (title or "").strip() or f"{day_type.title()} Menu {datetime.now().strftime('%b %Y')}"

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE mess_menu_weekly
        SET is_active = 0
        WHERE session_id = ? AND day_type = ?
    """, (session["id"], day_type))

    cur.execute("""
        INSERT INTO mess_menu_weekly (session_id, day_type, title)
        VALUES (?, ?, ?)
    """, (session["id"], day_type, title))

    menu_id = cur.lastrowid

    for day_name, _ in DAYS:
        cur.execute("""
            INSERT INTO mess_menu_items
            (weekly_menu_id, day_name)
            VALUES (?, ?)
        """, (menu_id, day_name))

    db.commit()
    db.close()


def save_weekly_menu(menu_id, form):
    db = get_db()
    cur = db.cursor()

    for day_name, _ in DAYS:
        cur.execute("""
            UPDATE mess_menu_items
            SET breakfast = ?, brunch = ?, lunch = ?, evening_snacks = ?, dinner = ?
            WHERE weekly_menu_id = ? AND day_name = ?
        """, (
            (form.get(f"{day_name}_breakfast") or "").strip(),
            (form.get(f"{day_name}_brunch") or "").strip(),
            (form.get(f"{day_name}_lunch") or "").strip(),
            (form.get(f"{day_name}_evening_snacks") or "").strip(),
            (form.get(f"{day_name}_dinner") or "").strip(),
            menu_id,
            day_name
        ))

    db.commit()
    db.close()
