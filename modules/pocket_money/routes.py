from flask import render_template, request, redirect, url_for, flash
from . import pocket_money_bp
from .models import get_wallet, create_wallet_if_not_exists
from .services import collect_money, spend_money, save_bill
from models.db import get_db


@pocket_money_bp.route("/collect", methods=["GET", "POST"])
def collect_search():
    if request.method == "POST":
        ledger_no = (request.form.get("ledger_no") or "").strip()
        if not ledger_no:
            flash("Please enter Ledger Number", "danger")
            return redirect(url_for("pocket_money.collect_search"))
        return redirect(url_for("pocket_money.collect", ledger_no=ledger_no))

    return render_template("pocket_money/collect_search.html")


@pocket_money_bp.route("/expense", methods=["GET", "POST"])
def expense_search():
    if request.method == "POST":
        ledger_no = (request.form.get("ledger_no") or "").strip()
        if not ledger_no:
            flash("Please enter Ledger Number", "danger")
            return redirect(url_for("pocket_money.expense_search"))
        return redirect(url_for("pocket_money.expense", ledger_no=ledger_no))

    return render_template("pocket_money/expense_search.html")


@pocket_money_bp.route("/ledger", methods=["GET", "POST"])
def ledger_search():
    if request.method == "POST":
        ledger_no = (request.form.get("ledger_no") or "").strip()
        if not ledger_no:
            flash("Please enter Ledger Number", "danger")
            return redirect(url_for("pocket_money.ledger_search"))
        return redirect(url_for("pocket_money.ledger", ledger_no=ledger_no))

    return render_template("pocket_money/ledger_search.html")


@pocket_money_bp.route("/")
def dashboard():
    db = get_db()
    q = request.args.get("q", "").strip()

    if q:
        wallets = db.execute("""
            SELECT w.*, s.student_name, s.class, s.section, s.status AS student_status
            FROM student_pocket_wallet w
            LEFT JOIN students s ON s.ledger_no = w.ledger_no
            WHERE w.ledger_no LIKE ?
            ORDER BY w.ledger_no
        """, (f"%{q}%",)).fetchall()
    else:
        wallets = db.execute("""
            SELECT w.*, s.student_name, s.class, s.section, s.status AS student_status
            FROM student_pocket_wallet w
            LEFT JOIN students s ON s.ledger_no = w.ledger_no
            ORDER BY w.ledger_no
        """).fetchall()

    total_wallets = len(wallets)
    total_balance = sum([w["current_balance"] or 0 for w in wallets])
    low_balance_count = len([w for w in wallets if (w["current_balance"] or 0) < 200])

    response = render_template(
        "pocket_money/dashboard.html",
        wallets=wallets,
        total_wallets=total_wallets,
        total_balance=total_balance,
        low_balance_count=low_balance_count
    )
    db.close()
    return response


@pocket_money_bp.route("/collect/<ledger_no>", methods=["GET", "POST"])
def collect(ledger_no):
    create_wallet_if_not_exists(ledger_no)
    db = get_db()
    student = db.execute("""
        SELECT ledger_no, student_name, class, section, status
        FROM students
        WHERE ledger_no = ?
    """, (ledger_no,)).fetchone()
    db.close()
    wallet = get_wallet(ledger_no)

    if request.method == "POST":
        amount = float(request.form["amount"])
        description = request.form.get("description", "")
        collect_money(
            ledger_no=ledger_no,
            amount=amount,
            description=description,
            created_by="ADMIN"
        )
        flash("Pocket money collected successfully.", "success")
        return redirect(url_for("pocket_money.ledger", ledger_no=ledger_no))

    return render_template(
        "pocket_money/collect.html",
        ledger_no=ledger_no,
        student=student,
        wallet=wallet
    )


@pocket_money_bp.route("/expense/<ledger_no>", methods=["GET", "POST"])
def expense(ledger_no):
    create_wallet_if_not_exists(ledger_no)
    db = get_db()
    student = db.execute("""
        SELECT ledger_no, student_name, class, section, status
        FROM students
        WHERE ledger_no = ?
    """, (ledger_no,)).fetchone()
    db.close()
    wallet = get_wallet(ledger_no)

    if request.method == "POST":
        category = request.form["category"]
        amount = float(request.form["amount"])
        description = request.form.get("description", "")
        bill_file = request.files.get("bill")
        bill_path = save_bill(bill_file)

        spend_money(
            ledger_no=ledger_no,
            category=category,
            amount=amount,
            description=description,
            bill_path=bill_path,
            created_by="ADMIN"
        )
        flash("Expense recorded successfully.", "success")
        return redirect(url_for("pocket_money.ledger", ledger_no=ledger_no))

    return render_template(
        "pocket_money/expense.html",
        ledger_no=ledger_no,
        student=student,
        wallet=wallet
    )


@pocket_money_bp.route("/ledger/<ledger_no>")
def ledger(ledger_no):
    create_wallet_if_not_exists(ledger_no)
    db = get_db()
    date_from = (request.args.get("from") or "").strip()
    date_to = (request.args.get("to") or "").strip()
    student = db.execute("""
        SELECT ledger_no, student_name, class, section, status
        FROM students
        WHERE ledger_no = ?
    """, (ledger_no,)).fetchone()
    wallet = get_wallet(ledger_no)
    query = """
        SELECT *
        FROM pocket_money_transactions
        WHERE ledger_no = ?
    """
    params = [ledger_no]

    if date_from:
        query += " AND date(created_at) >= date(?)"
        params.append(date_from)
    if date_to:
        query += " AND date(created_at) <= date(?)"
        params.append(date_to)

    query += " ORDER BY created_at DESC"
    transactions = db.execute(query, tuple(params)).fetchall()
    response = render_template(
        "pocket_money/ledger.html",
        wallet=wallet,
        txns=transactions,
        ledger_no=ledger_no,
        student=student,
        date_from=date_from,
        date_to=date_to,
    )
    db.close()
    return response


@pocket_money_bp.route("/transaction/<int:txn_id>")
def view_transaction(txn_id):
    db = get_db()
    txn = db.execute("""
        SELECT *
        FROM pocket_money_transactions
        WHERE id = ?
    """, (txn_id,)).fetchone()

    if not txn:
        db.close()
        flash("Transaction not found.", "danger")
        return redirect(url_for("pocket_money.dashboard"))

    response = render_template("pocket_money/view_transaction.html", txn=txn)
    db.close()
    return response


@pocket_money_bp.route("/create-wallet", methods=["POST"])
def create_wallet():
    ledger_no = request.form.get("ledger_no")

    if not ledger_no:
        flash("Ledger number is required.", "danger")
        return redirect(url_for("pocket_money.dashboard"))

    create_wallet_if_not_exists(ledger_no)
    flash(f"Wallet created for Ledger {ledger_no}.", "success")
    return redirect(url_for("pocket_money.ledger", ledger_no=ledger_no))


@pocket_money_bp.route("/ensure-wallet/<ledger_no>")
def ensure_wallet(ledger_no):
    create_wallet_if_not_exists(ledger_no)
    return redirect(url_for("pocket_money.ledger", ledger_no=ledger_no))
