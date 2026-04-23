import sqlite3

conn = sqlite3.connect("database/hostel.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS student_pocket_wallet (
    ledger_no TEXT PRIMARY KEY,
    opening_balance REAL DEFAULT 0,
    current_balance REAL DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS pocket_money_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_no TEXT NOT NULL,
    txn_type TEXT CHECK(txn_type IN ('COLLECT','EXPENSE')),
    category TEXT,
    amount REAL NOT NULL,
    description TEXT,
    bill_path TEXT,
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Pocket Money tables initialized successfully.")
