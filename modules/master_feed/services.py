from models.db import get_db


# ---------- ROUTINES ----------
def get_all_routines():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM master_routines
        WHERE is_deleted = 0
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    db.close()
    return rows


def create_routine(title, description):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO master_routines (title, description, is_deleted)
        VALUES (?, ?, 0)
    """, (title, description))
    db.commit()
    db.close()


def can_delete_routine(routine_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id FROM master_routines
        WHERE id = ? AND is_deleted = 0
    """, (routine_id,))
    row = cur.fetchone()
    db.close()

    if not row:
        return False, "Routine not found"

    # Future child check (logs, attendance etc.)
    return True, ""


def soft_delete_routine(routine_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE master_routines
        SET is_deleted = 1
        WHERE id = ?
    """, (routine_id,))
    db.commit()
    db.close()


# ---------- FORMS ----------
def get_all_forms():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM master_forms
        WHERE is_deleted = 0
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    db.close()
    return rows


def create_form(form_name, target_url):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO master_forms (form_name, target_url, is_deleted)
        VALUES (?, ?, 0)
    """, (form_name, target_url))
    db.commit()
    db.close()


def can_delete_form(form_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id FROM master_forms
        WHERE id = ? AND is_deleted = 0
    """, (form_id,))
    row = cur.fetchone()
    db.close()

    if not row:
        return False, "Form not found"

    # Future child check (submissions, usage)
    return True, ""


def soft_delete_form(form_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE master_forms
        SET is_deleted = 1
        WHERE id = ?
    """, (form_id,))
    db.commit()
    db.close()
