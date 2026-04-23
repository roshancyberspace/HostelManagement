from models.db import get_db

def init_staff_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS staff_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        designation TEXT NOT NULL,
        department TEXT DEFAULT 'HOSTEL',
        phone TEXT,
        alternate_phone TEXT,
        email TEXT,
        address TEXT,
        joining_date TEXT,
        salary_monthly REAL DEFAULT 0,
        status TEXT DEFAULT 'ACTIVE',
        remarks TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
