from flask import render_template, request, redirect, url_for, flash
from . import parent_portal_bp
from models.db import get_db


@parent_portal_bp.route("/wallet", methods=["GET", "POST"])
def wallet_search():
    if request.method == "POST":
        ledger_no = (request.form.get("ledger_no") or "").strip()
        if not ledger_no:
            flash("Please enter Ledger Number", "danger")
            return redirect(url_for("parent_portal.wallet_search"))

        return redirect(url_for("parent_portal.wallet_view", ledger_no=ledger_no))

    return render_template("parent_portal/wallet_search.html")


@parent_portal_bp.route("/wallet/<ledger_no>")
def wallet_view(ledger_no):
    db = get_db()

    student = db.execute("""
        SELECT ledger_no, student_name, class, section, status
        FROM students
        WHERE ledger_no = ?
    """, (ledger_no,)).fetchone()

    wallet = db.execute("""
        SELECT * FROM student_pocket_wallet
        WHERE ledger_no = ?
    """, (ledger_no,)).fetchone()

    txns = db.execute("""
        SELECT *
        FROM pocket_money_transactions
        WHERE ledger_no = ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (ledger_no,)).fetchall()

    response = render_template(
        "parent_portal/wallet.html",
        student=student,
        wallet=wallet,
        txns=txns,
        ledger_no=ledger_no
    )
    db.close()
    return response
