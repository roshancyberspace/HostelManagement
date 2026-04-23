from models.db import get_db
from datetime import datetime

ALLOWED_TARGETS = ("ROOM", "COMMON")

def add_inspection(target_type, target_id, insp_type, remarks, damage, fine, date=None):
    """
    target_type : ROOM | COMMON
    target_id   : rooms.id or common_areas.id
    insp_type   : PRE | POST | ROUTINE
    """

    if target_type not in ALLOWED_TARGETS:
        raise ValueError("Invalid inspection target type")

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    db.execute("""
        INSERT INTO inspections
        (target_type, target_id, inspection_type, remarks, damage, fine, inspected_on)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (target_type, target_id, insp_type, remarks, damage, fine, date))
    db.commit()


def get_history(target_type, target_id):
    if target_type not in ALLOWED_TARGETS:
        raise ValueError("Invalid inspection target type")

    return get_db().execute("""
        SELECT *
        FROM inspections
        WHERE target_type=? AND target_id=?
        ORDER BY inspected_on DESC
    """, (target_type, target_id)).fetchall()


def get_pre_post(target_type, target_id):
    if target_type not in ALLOWED_TARGETS:
        raise ValueError("Invalid inspection target type")

    db = get_db()

    pre = db.execute("""
        SELECT *
        FROM inspections
        WHERE target_type=? AND target_id=? AND inspection_type='PRE'
        ORDER BY inspected_on DESC
        LIMIT 1
    """, (target_type, target_id)).fetchone()

    post = db.execute("""
        SELECT *
        FROM inspections
        WHERE target_type=? AND target_id=? AND inspection_type='POST'
        ORDER BY inspected_on DESC
        LIMIT 1
    """, (target_type, target_id)).fetchone()

    return pre, post
