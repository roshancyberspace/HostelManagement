import sqlite3
from config import DB_PATH


def init_hostel_timetable_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hostel_timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            day_type TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            start_time TIME,
            end_time TIME,
            time_source TEXT NOT NULL,
            sequence_no INTEGER NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """)

    conn.commit()
    conn.close()
