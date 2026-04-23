import sqlite3
from models.db import get_db

def get_wallet(ledger_no):
    db = get_db()
    wallet = db.execute(
        "SELECT * FROM student_pocket_wallet WHERE ledger_no = ?",
        (ledger_no,)
    ).fetchone()
    db.close()
    return wallet

def create_wallet_if_not_exists(ledger_no):
    db = get_db()
    db.execute("""
        INSERT OR IGNORE INTO student_pocket_wallet (ledger_no)
        VALUES (?)
    """, (ledger_no,))
    db.commit()
    db.close()
