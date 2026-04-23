from models.db import get_db


def init_laundry_tables():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS laundry_weekly_routine (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            title TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS laundry_routine_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routine_id INTEGER NOT NULL,
            day_name TEXT NOT NULL,
            deposit TEXT,
            deliver TEXT,
            FOREIGN KEY (routine_id) REFERENCES laundry_weekly_routine(id)
        )
    """)

    db.commit()
    db.close()
