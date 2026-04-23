from models.db import get_db


def init_laundry_register_table():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS laundry_register (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            ledger_no TEXT NOT NULL,
            student_name TEXT NOT NULL,
            class_section TEXT NOT NULL,
            items_given TEXT,
            date_given DATE,
            items_returned TEXT,
            date_returned DATE,
            status TEXT DEFAULT 'GIVEN',
            remarks TEXT,
            issue_photo_path TEXT DEFAULT '',
            return_photo_path TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("PRAGMA table_info(laundry_register)")
    existing_columns = {row["name"] for row in cur.fetchall()}
    if "issue_photo_path" not in existing_columns:
        cur.execute("ALTER TABLE laundry_register ADD COLUMN issue_photo_path TEXT DEFAULT ''")
    if "return_photo_path" not in existing_columns:
        cur.execute("ALTER TABLE laundry_register ADD COLUMN return_photo_path TEXT DEFAULT ''")

    db.commit()
    db.close()
