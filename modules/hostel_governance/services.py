from models.db import get_db
from datetime import datetime

# ----------------- NOTICES -----------------

def create_notice(title, content, scope, created_by):
    db = get_db()
    db.execute("""
        INSERT INTO hostel_notices (title, content, target_scope, created_by, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (title, content, scope, created_by, datetime.now().isoformat()))
    db.commit()


def get_all_notices():
    db = get_db()
    return db.execute("""
        SELECT * FROM hostel_notices
        ORDER BY id DESC
    """).fetchall()


# ----------------- ACKNOWLEDGEMENT -----------------

def acknowledge_notice(notice_id, ledger_no):
    db = get_db()
    db.execute("""
        INSERT INTO hostel_notice_ack (notice_id, ledger_no, acknowledged_at)
        VALUES (?, ?, ?)
    """, (notice_id, ledger_no, datetime.now().isoformat()))
    db.commit()


def get_acknowledgements(notice_id):
    db = get_db()
    return db.execute("""
        SELECT * FROM hostel_notice_ack
        WHERE notice_id = ?
    """, (notice_id,)).fetchall()


# ----------------- DECISIONS -----------------

def record_decision(ledger_no, decision, reference, decided_by):
    db = get_db()
    db.execute("""
        INSERT INTO hostel_decisions
        (ledger_no, decision, reference, decided_by, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (ledger_no, decision, reference, decided_by, datetime.now().isoformat()))
    db.commit()


def get_all_decisions():
    db = get_db()
    return db.execute("""
        SELECT * FROM hostel_decisions
        ORDER BY id DESC
    """).fetchall()
