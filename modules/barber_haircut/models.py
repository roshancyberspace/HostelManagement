from models.db import get_db

def init_barber_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS barber_haircut_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ledger_no TEXT NOT NULL,
        student_name TEXT NOT NULL,
        class_name TEXT,
        section TEXT,
        haircut_month TEXT NOT NULL,
        haircut_date TEXT NOT NULL,
        barber_name TEXT DEFAULT '',
        before_photo_path TEXT DEFAULT '',
        after_photo_path TEXT DEFAULT '',
        remark TEXT DEFAULT '',
        status TEXT DEFAULT 'DONE',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
