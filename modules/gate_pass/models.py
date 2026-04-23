from models.db import get_db

def init_gate_pass_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS gate_passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate_pass_no TEXT UNIQUE,
            ledger_no TEXT NOT NULL,

            purpose TEXT NOT NULL,
            relation TEXT,

            out_datetime TEXT NOT NULL,
            expected_return_datetime TEXT NOT NULL,
            actual_return_datetime TEXT,

            status TEXT CHECK(
                status IN ('PENDING','APPROVED','RETURNED','VIOLATION')
            ) DEFAULT 'PENDING',

            approved_by TEXT,
            remarks TEXT,

            created_at TEXT NOT NULL
        )
    """)
    db.commit()
