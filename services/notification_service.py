from models.db import get_db
from datetime import date, timedelta

# ======================================================
# NOTIFICATION COUNTERS (DASHBOARD / SIDEBAR)
# ======================================================
def get_notification_counts():
    db = get_db()
    overdue_date = date.today() - timedelta(days=7)

    # Room damages
    room_damages = db.execute(
        "SELECT COUNT(*) FROM rooms WHERE status='DAMAGED'"
    ).fetchone()[0]

    # Overdue inspections
    overdue_inspections = db.execute("""
        SELECT COUNT(*)
        FROM rooms r
        WHERE (
            SELECT MAX(inspected_on)
            FROM inspections
            WHERE target_type='ROOM' AND target_id=r.id
        ) < ?
        OR NOT EXISTS (
            SELECT 1 FROM inspections
            WHERE target_type='ROOM' AND target_id=r.id
        )
    """, (overdue_date,)).fetchone()[0]

    # Gate Pass – Pending
    try:
        gate_pass_pending = db.execute("""
            SELECT COUNT(*)
            FROM gate_pass
            WHERE status = 'PENDING'
        """).fetchone()[0]
    except Exception:
        gate_pass_pending = 0

    # Gate Pass – Violations
    try:
        gate_pass_violations = db.execute("""
            SELECT COUNT(*)
            FROM gate_pass
            WHERE status = 'VIOLATION'
        """).fetchone()[0]
    except Exception:
        gate_pass_violations = 0

    db.close()

    return {
        "damages": room_damages,
        "overdue": overdue_inspections,
        "gate_pass_pending": gate_pass_pending,
        "gate_pass_violations": gate_pass_violations
    }


# ======================================================
# PARENT NOTIFICATION (SMS / WHATSAPP – SAFE STUB)
# ======================================================
def notify_parent(ledger_no, message):
    """
    SAFE placeholder for SMS / WhatsApp.
    Does NOT break system if API not configured.
    """
    try:
        db = get_db()
        parent = db.execute("""
            SELECT
                p.father_mobile_1,
                p.father_mobile_2,
                p.mother_mobile_1,
                p.mother_mobile_2
            FROM student_parents p
            JOIN students s ON s.id = p.student_id
            WHERE s.ledger_no = ?
            LIMIT 1
        """, (ledger_no,)).fetchone()
        db.close()

        if not parent:
            return False

        mobile = (
            parent["father_mobile_1"]
            or parent["father_mobile_2"]
            or parent["mother_mobile_1"]
            or parent["mother_mobile_2"]
        )

        if not mobile:
            return False

        # 🔔 FUTURE INTEGRATION POINT
        # send_sms(mobile, message)
        # send_whatsapp(mobile, message)

        print(f"[PARENT NOTIFY] {ledger_no}: {message}")
        return True

    except Exception as e:
        print("Parent notification failed:", e)
        return False
