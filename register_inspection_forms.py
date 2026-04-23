from models.db import get_db

db = get_db()
cur = db.cursor()

forms = [
    ("Room Inspection", "/inspection/room"),
    ("Common Area Inspection", "/inspection/common"),
    ("Recovery Ledger", "/inspection/recovery-ledger"),
    ("Inspection Alerts", "/inspection-alerts"),
]

for name, url in forms:
    cur.execute("""
        INSERT INTO master_forms (form_name, target_url)
        SELECT ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM master_forms WHERE target_url = ?
        )
    """, (name, url, url))

db.commit()
db.close()

print("✅ Inspection forms registered in Master Feed")
