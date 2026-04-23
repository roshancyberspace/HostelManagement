from models.db import get_db

def generate_ledger_no():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT MAX(id) FROM students")
    last_id = cur.fetchone()[0] or 0

    ledger_no = f"L-{last_id + 1001}"
    db.close()
    return ledger_no
