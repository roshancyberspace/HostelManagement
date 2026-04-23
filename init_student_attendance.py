from models.db import get_db

def init_student_attendance():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        ledger_no TEXT NOT NULL,
        attendance_date TEXT NOT NULL,
        day_type TEXT NOT NULL,

        slot TEXT NOT NULL,
        status TEXT NOT NULL,

        remarks TEXT,
        application_file TEXT,

        is_gatepass INTEGER DEFAULT 0,

        snapshot TEXT NOT NULL,

        marked_by TEXT NOT NULL,
        marked_at TEXT NOT NULL,

        corrected INTEGER DEFAULT 0,
        correction_reason TEXT,

        UNIQUE(ledger_no, attendance_date, slot)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ student_attendance table created successfully")

if __name__ == "__main__":
    init_student_attendance()
