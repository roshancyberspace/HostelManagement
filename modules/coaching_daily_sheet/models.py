from models.db import get_db

def init_tables():
    """
    Create required tables if not exist.
    """
    conn = get_db()
    cur = conn.cursor()

    # Weekly Master - Coaching
    cur.execute("""
    CREATE TABLE IF NOT EXISTS coaching_weekly_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_name TEXT NOT NULL,
        class_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        teacher_name TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Weekly Master - Study Duty
    cur.execute("""
    CREATE TABLE IF NOT EXISTS study_duty_weekly_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_name TEXT NOT NULL,
        class_group TEXT NOT NULL,
        floor_place TEXT NOT NULL,
        teacher_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Daily Sheet - Coaching
    cur.execute("""
    CREATE TABLE IF NOT EXISTS coaching_daily_sheet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sheet_date TEXT NOT NULL,
        day_name TEXT NOT NULL,
        class_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        teacher_name TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        remark TEXT DEFAULT '',
        updated_by TEXT DEFAULT 'SYSTEM',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Daily Sheet - Study Duty
    cur.execute("""
    CREATE TABLE IF NOT EXISTS study_duty_daily_sheet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sheet_date TEXT NOT NULL,
        day_name TEXT NOT NULL,
        class_group TEXT NOT NULL,
        floor_place TEXT NOT NULL,
        teacher_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        remark TEXT DEFAULT '',
        updated_by TEXT DEFAULT 'SYSTEM',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
