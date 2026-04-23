from models.db import get_db

def init_student_tables():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ledger_no TEXT UNIQUE,
        student_name TEXT,
        class TEXT,
        section TEXT,
        session_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_biodata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        dob DATE,
        room_no TEXT,
        class_of_admission TEXT,
        date_of_admission DATE,
        hostel_reporting_date DATE,
        permanent_address TEXT,
        student_photo TEXT,
        personal_fund_amt REAL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_parents (
        student_id INTEGER PRIMARY KEY,
        father_name TEXT,
        father_mobile_1 TEXT,
        father_mobile_2 TEXT,
        father_photo TEXT,
        mother_name TEXT,
        mother_mobile_1 TEXT,
        mother_mobile_2 TEXT,
        mother_photo TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_guardians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        name TEXT,
        relation TEXT,
        mobile_1 TEXT,
        mobile_2 TEXT,
        address TEXT,
        photo TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    db.commit()
    db.close()
