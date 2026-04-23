from models.db import get_db

def init_student_profile_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS student_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_no TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            class TEXT NOT NULL,
            section TEXT NOT NULL,
            roll_no TEXT,
            father_name TEXT,
            mother_name TEXT,
            guardian_contact TEXT,
            joining_date TEXT NOT NULL,
            leaving_date TEXT,
            status TEXT DEFAULT 'ACTIVE',
            remarks TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    db.commit()


def init_student_behaviour_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS student_behaviour_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_no TEXT NOT NULL,
            behaviour_type TEXT CHECK(behaviour_type IN ('GOOD','BAD')) NOT NULL,
            severity TEXT CHECK(severity IN ('LOW','MEDIUM','HIGH','CRITICAL')) NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            recorded_by TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        )
    """)
    db.commit()
