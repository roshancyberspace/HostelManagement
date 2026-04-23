from models.db import get_db

db = get_db()
cur = db.cursor()

forms = [
    ("Stock Dashboard", "/stock/"),
    ("Stock Master", "/stock/master"),
    ("Room Stock", "/stock/room"),
    ("Area Stock", "/stock/area"),
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

print("✅ Stock forms registered in Master Feed")
