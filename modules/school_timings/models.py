import sqlite3
from config import DB_PATH


def init_school_timings_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS school_timings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            day_type TEXT NOT NULL,
            reporting_time TIME NOT NULL,
            recess_time TIME NOT NULL,
            dispersal_senior TIME NOT NULL,
            dispersal_junior TIME NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """)

    conn.commit()
    conn.close()
