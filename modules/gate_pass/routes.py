from flask import render_template, request, redirect, session, flash, url_for
from . import gate_pass_bp
from .services import *
from modules.student_profile.services import get_student

@gate_pass_bp.route("/gate-pass")
def list_gate_pass():
    return render_template(
        "gate_pass/list.html",
        passes=get_all_gate_passes()
    )

@gate_pass_bp.route("/gate-pass/create", methods=["GET","POST"])
def create():
    if request.method == "POST":
        try:
            create_gate_pass(request.form, session["user"]["name"])
            flash("Gate Pass created successfully.", "success")
            return redirect("/gate-pass")
        except Exception as exc:
            flash(str(exc), "danger")
            ledger = request.form.get("ledger_no")
            student = get_student(ledger) if ledger else None
            return render_template("gate_pass/create.html", student=student, form_data=request.form)

    ledger = request.args.get("ledger_no")
    student = get_student(ledger) if ledger else None
    return render_template("gate_pass/create.html", student=student, form_data={})

@gate_pass_bp.route("/gate-pass/<int:gp_id>")
def view(gp_id):
    context = get_gate_pass_context(gp_id)
    if not context:
        flash("Gate Pass not found.", "danger")
        return redirect("/gate-pass")

    return render_template(
        "gate_pass/view.html",
        gp=context["gp"],
        student=context["student"],
        wallet=context["wallet"]
    )

@gate_pass_bp.route("/gate-pass/<int:gp_id>/approve", methods=["GET", "POST"])
def approve(gp_id):
    try:
        override_reason = request.form.get("override_reason") if request.method == "POST" else None
        update_status(gp_id, "APPROVED", session["user"]["name"], override_reason)
        flash("Gate Pass approved.", "success")
    except Exception as exc:
        flash(str(exc), "danger")
    return redirect(f"/gate-pass/{gp_id}")

@gate_pass_bp.route("/gate-pass/<int:gp_id>/return")
def returned(gp_id):
    mark_return(gp_id, False, session["user"]["name"])
    flash("Student marked as returned.", "success")
    return redirect(f"/gate-pass/{gp_id}")

@gate_pass_bp.route("/gate-pass/<int:gp_id>/violation")
def violation(gp_id):
    mark_return(gp_id, True, session["user"]["name"])
    flash("Violation recorded.", "warning")
    return redirect(f"/gate-pass/{gp_id}")

@gate_pass_bp.route("/gate-pass/<int:gp_id>/print")
def print_view(gp_id):
    context = get_gate_pass_context(gp_id)
    if not context:
        return "Gate Pass not found", 404
    return render_template(
        "gate_pass/print.html",
        gp=context["gp"],
        student=context["student"]
    )

from models.db import get_db

@gate_pass_bp.route("/print-with-pocket/<int:gp_id>")
def print_with_pocket(gp_id):
    db = get_db()

    gp = db.execute("""
        SELECT * FROM gate_passes WHERE id = ?
    """, (gp_id,)).fetchone()

    if not gp:
        return "Gate Pass not found", 404

    # Student
    student = get_student(gp["ledger_no"])

    # Pocket Wallet
    wallet = db.execute("""
        SELECT current_balance
        FROM student_pocket_wallet
        WHERE ledger_no = ?
    """, (gp["ledger_no"],)).fetchone()

    # Pocket Transactions (last 5)
    txns = db.execute("""
        SELECT txn_type, amount, category, created_at
        FROM pocket_money_transactions
        WHERE ledger_no = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, (gp["ledger_no"],)).fetchall()

    total_collected = db.execute("""
        SELECT COALESCE(SUM(amount),0) s
        FROM pocket_money_transactions
        WHERE ledger_no = ? AND txn_type = 'COLLECT'
    """, (gp["ledger_no"],)).fetchone()["s"]

    total_spent = db.execute("""
        SELECT COALESCE(SUM(amount),0) s
        FROM pocket_money_transactions
        WHERE ledger_no = ? AND txn_type = 'EXPENSE'
    """, (gp["ledger_no"],)).fetchone()["s"]

    return render_template(
        "gate_pass/print_with_pocket.html",
        gp=gp,
        student=student,
        wallet=wallet,
        txns=txns,
        total_collected=total_collected,
        total_spent=total_spent
    )
