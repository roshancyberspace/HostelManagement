import sqlite3
from config import DB_PATH


def init_calendar_rules_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS calendar_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            from_date DATE NOT NULL,
            to_date DATE NOT NULL,
            day_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """)

    conn.commit()
    conn.close()
