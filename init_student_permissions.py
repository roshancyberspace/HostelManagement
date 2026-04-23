from models.db import get_db

db = get_db()
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS student_self_going (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    allowed INTEGER DEFAULT 0,
    valid_from DATE,
    valid_to DATE,
    application_file TEXT,
    remarks TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS student_device_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    device_type TEXT, -- MOBILE / LAPTOP
    allowed INTEGER DEFAULT 0,
    application_file TEXT,
    remarks TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()
db.close()

print("✅ Student Permissions tables created")
