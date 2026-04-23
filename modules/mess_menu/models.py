from models.db import get_db


def init_mess_menu_tables():
    db = get_db()
    cur = db.cursor()

    # Weekly menu header
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mess_menu_weekly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            day_type TEXT NOT NULL, -- WORKING / SUNDAY / HOLIDAY
            title TEXT,
            effective_from DATE,
            effective_to DATE,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Weekly menu rows (7 days)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mess_menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weekly_menu_id INTEGER NOT NULL,
            day_name TEXT NOT NULL, -- MONDAY..SUNDAY
            breakfast TEXT,
            brunch TEXT,
            lunch TEXT,
            evening_snacks TEXT,
            dinner TEXT,
            FOREIGN KEY (weekly_menu_id) REFERENCES mess_menu_weekly(id)
        )
    """)

    db.commit()
    db.close()
