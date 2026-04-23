import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from models.db import get_db


# --------------------------------------------------
# SAVE PERMISSION FILE
# --------------------------------------------------
def save_permission_file(file, ledger, folder):
    if not file or file.filename == "":
        return None

    base_path = os.path.join(
        current_app.root_path,
        "static", "uploads", "permissions", ledger, folder
    )
    os.makedirs(base_path, exist_ok=True)

    filename = secure_filename(file.filename)
    path = os.path.join(base_path, filename)
    file.save(path)

    return f"uploads/permissions/{ledger}/{folder}/{filename}"


# --------------------------------------------------
# SELF GOING HISTORY
# --------------------------------------------------
def get_self_going_history(student_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM student_self_going
        WHERE student_id = ?
        ORDER BY is_active DESC, created_at DESC
    """, (student_id,))

    rows = cur.fetchall()
    db.close()
    return rows


# --------------------------------------------------
# DEVICE HISTORY
# --------------------------------------------------
def get_device_history(student_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM student_device_permission
        WHERE student_id = ?
        ORDER BY is_active DESC, created_at DESC
    """, (student_id,))

    rows = cur.fetchall()
    db.close()
    return rows


# --------------------------------------------------
# REVOKE SELF GOING
# --------------------------------------------------
def revoke_self_going(permission_id, reason):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE student_self_going
        SET allowed = 0,
            is_active = 0,
            revoked_reason = ?,
            revoked_at = ?
        WHERE id = ?
    """, (
        reason,
        datetime.now(),
        permission_id
    ))

    db.commit()
    db.close()


# --------------------------------------------------
# REVOKE DEVICE PERMISSION
# --------------------------------------------------
def revoke_device(permission_id, reason):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE student_device_permission
        SET allowed = 0,
            is_active = 0,
            revoked_reason = ?,
            revoked_at = ?
        WHERE id = ?
    """, (
        reason,
        datetime.now(),
        permission_id
    ))

    db.commit()
    db.close()


def get_active_self_going(student_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM student_self_going
        WHERE student_id = ?
          AND allowed = 1
          AND COALESCE(is_active, 1) = 1
        ORDER BY created_at DESC
        LIMIT 1
    """, (student_id,))
    row = cur.fetchone()
    db.close()
    return row


def get_active_device_permission(student_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM student_device_permission
        WHERE student_id = ?
          AND allowed = 1
          AND COALESCE(is_active, 1) = 1
        ORDER BY created_at DESC
        LIMIT 1
    """, (student_id,))
    row = cur.fetchone()
    db.close()
    return row


def get_permission_dashboard_metrics():
    db = get_db()
    cur = db.cursor()

    metrics = {
        "active_self_going": cur.execute("""
            SELECT COUNT(*) AS total
            FROM student_self_going
            WHERE allowed = 1 AND COALESCE(is_active, 1) = 1
        """).fetchone()["total"],
        "active_device": cur.execute("""
            SELECT COUNT(*) AS total
            FROM student_device_permission
            WHERE allowed = 1 AND COALESCE(is_active, 1) = 1
        """).fetchone()["total"],
        "self_going_total": cur.execute("SELECT COUNT(*) AS total FROM student_self_going").fetchone()["total"],
        "device_total": cur.execute("SELECT COUNT(*) AS total FROM student_device_permission").fetchone()["total"],
    }

    db.close()
    return metrics


def get_recent_permission_activity(limit=8):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM (
            SELECT
                'SELF_GOING' AS permission_type,
                s.ledger_no,
                s.student_name,
                s.class,
                sg.allowed,
                sg.is_active,
                sg.valid_from,
                sg.valid_to,
                sg.remarks,
                sg.revoked_at,
                sg.created_at
            FROM student_self_going sg
            LEFT JOIN students s ON s.id = sg.student_id

            UNION ALL

            SELECT
                'DEVICE' AS permission_type,
                s.ledger_no,
                s.student_name,
                s.class,
                dp.allowed,
                dp.is_active,
                NULL AS valid_from,
                NULL AS valid_to,
                COALESCE(dp.device_type || ': ', '') || COALESCE(dp.remarks, '') AS remarks,
                dp.revoked_at,
                dp.created_at
            FROM student_device_permission dp
            LEFT JOIN students s ON s.id = dp.student_id
        ) recent_permissions
        ORDER BY recent_permissions.created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    db.close()
    return rows
