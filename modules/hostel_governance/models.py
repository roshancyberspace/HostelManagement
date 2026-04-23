from models.db import get_db
from datetime import datetime

def init_governance_tables():
    db = get_db()
    cursor = db.cursor()

    # Notices / Circulars
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hostel_notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            target_scope TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Notice acknowledgement (insert-only)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hostel_notice_ack (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notice_id INTEGER NOT NULL,
            ledger_no TEXT NOT NULL,
            acknowledged_at TEXT NOT NULL
        )
    """)

    # Decision / Escalation register
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hostel_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_no TEXT NOT NULL,
            decision TEXT NOT NULL,
            reference TEXT,
            decided_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    db.commit()
