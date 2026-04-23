import os
from werkzeug.utils import secure_filename
from models.db import get_db
from config import POCKET_MONEY_MIN_BALANCE_FOR_GATEPASS

UPLOAD_FOLDER = "static/uploads/pocket_money"


def save_bill(file):
    if not file or file.filename == "":
        return None

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return path


def create_wallet_if_not_exists(ledger_no):
    db = get_db()
    db.execute("""
        INSERT OR IGNORE INTO student_pocket_wallet (ledger_no)
        VALUES (?)
    """, (ledger_no,))
    db.commit()
    db.close()


def get_wallet(ledger_no):
    db = get_db()
    wallet = db.execute("""
        SELECT *
        FROM student_pocket_wallet
        WHERE ledger_no = ?
    """, (ledger_no,)).fetchone()
    db.close()
    return wallet


def get_wallet_balance(ledger_no):
    wallet = get_wallet(ledger_no)
    return wallet["current_balance"] if wallet else 0


def collect_money(ledger_no, amount, description, created_by):
    create_wallet_if_not_exists(ledger_no)
    db = get_db()
    db.execute("""
        INSERT INTO pocket_money_transactions
        (ledger_no, txn_type, category, amount, description, created_by)
        VALUES (?, 'COLLECT', 'PARENT', ?, ?, ?)
    """, (ledger_no, amount, description, created_by))

    db.execute("""
        UPDATE student_pocket_wallet
        SET current_balance = current_balance + ?
        WHERE ledger_no = ?
    """, (amount, ledger_no))

    db.commit()
    db.close()


def spend_money(ledger_no, category, amount, description, bill_path, created_by):
    create_wallet_if_not_exists(ledger_no)
    db = get_db()
    db.execute("""
        INSERT INTO pocket_money_transactions
        (ledger_no, txn_type, category, amount, description, bill_path, created_by)
        VALUES (?, 'EXPENSE', ?, ?, ?, ?, ?)
    """, (ledger_no, category, amount, description, bill_path, created_by))

    db.execute("""
        UPDATE student_pocket_wallet
        SET current_balance = current_balance - ?
        WHERE ledger_no = ?
    """, (amount, ledger_no))

    db.commit()
    db.close()


def is_wallet_clear_for_gatepass(ledger_no):
    balance = get_wallet_balance(ledger_no)
    return balance >= POCKET_MONEY_MIN_BALANCE_FOR_GATEPASS


def get_wallet_block_reason(ledger_no):
    wallet = get_wallet(ledger_no)

    if not wallet:
        return "Pocket money wallet not created. Please create wallet first."

    if wallet["current_balance"] < POCKET_MONEY_MIN_BALANCE_FOR_GATEPASS:
        return (
            f"Pocket money balance is below Rs.{POCKET_MONEY_MIN_BALANCE_FOR_GATEPASS}. "
            "Please recharge before issuing Gate Pass."
        )

    return None
