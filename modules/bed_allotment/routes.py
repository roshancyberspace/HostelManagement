from flask import render_template, request, redirect, flash
from . import bed_allotment_bp
from models.db import get_db

from .service import (
    get_active_student,
    student_has_active_bed,
    bed_is_occupied,
    allot_bed,
    vacate_bed,
    get_beds_for_allotment,
    get_occupancy,
    get_history
)


# ==========================================================
# BED INVENTORY (VIEW ONLY)
# URL: /bed-allotment/inventory
# ==========================================================
@bed_allotment_bp.route('/inventory', methods=['GET'])
def bed_inventory():
    db = get_db()

    beds = db.execute("""
        SELECT
            f.floor_name AS floor_name,
            r.room_no AS room_no,
            b.bed_no AS bed_no,
            b.status AS status
        FROM beds b
        JOIN rooms r ON r.id = b.room_id
        JOIN floors f ON f.id = r.floor_id
        WHERE UPPER(r.ac_type) = 'AC'
          AND r.bed_capacity > 0
        ORDER BY
          CASE f.floor_name
            WHEN 'Ground Floor' THEN 1
            WHEN 'First Floor' THEN 2
            WHEN 'Second Floor' THEN 3
            WHEN 'Third Floor' THEN 4
            ELSE 99
          END,
          CAST(r.room_no AS INTEGER),
          CAST(b.bed_no AS INTEGER)
    """).fetchall()

    return render_template("bed_inventory.html", beds=beds)


# ==========================================================
# BED ALLOTMENT (ALLOT + VACATE)
# URL: /bed-allotment/allot
# ==========================================================
@bed_allotment_bp.route('/allot', methods=['GET', 'POST'])
def bed_allot():
    db = get_db()
    student = None

    if request.method == 'POST':
        action = (request.form.get("action") or "ALLOT").strip().upper()
        ledger = (request.form.get("ledger") or "").strip()

        if not ledger:
            flash("Ledger Number is required", "danger")
            return redirect(request.url)

        student = get_active_student(db, ledger)

        if not student:
            flash("Invalid Ledger Number", "danger")
            return redirect(request.url)

        # ✅ Only ACTIVE students allowed
        if str(student.get("status", "")).upper() != "ACTIVE":
            flash("Only ACTIVE hostel students can be allotted beds", "danger")
            return redirect(request.url)

        # ---------------- VACATE ----------------
        if action == "VACATE":
            reason = (request.form.get("vacate_reason") or "VACATED").strip()
            try:
                vacate_bed(db, ledger, reason)
                db.commit()
                flash("Bed vacated successfully ✅", "success")
            except Exception as e:
                db.rollback()
                flash(str(e), "danger")
            return redirect(request.url)

        # ---------------- ALLOT ----------------
        bed_id = request.form.get("bed_id")
        if not bed_id:
            flash("Please select a bed", "danger")
            return redirect(request.url)

        try:
            if student_has_active_bed(db, ledger):
                flash("Student already has an active bed", "danger")
                return redirect(request.url)

            if bed_is_occupied(db, int(bed_id)):
                flash("Bed already occupied", "danger")
                return redirect(request.url)

            allot_bed(db, ledger, int(bed_id))
            db.commit()
            flash("Bed allotted successfully ✅", "success")
            return redirect(request.url)

        except Exception as e:
            db.rollback()
            flash(str(e), "danger")
            return redirect(request.url)

    # GET
    beds = get_beds_for_allotment(db)
    return render_template("bed_allot.html", beds=beds, student=student)


# ==========================================================
# CURRENT OCCUPANCY
# URL: /bed-allotment/occupancy
# ==========================================================
@bed_allotment_bp.route('/occupancy', methods=['GET'])
def bed_occupancy():
    db = get_db()
    data = get_occupancy(db)
    return render_template("bed_occupancy.html", data=data)


# ==========================================================
# BED HISTORY (FORM SEARCH PAGE)
# URL: /bed-allotment/history
# ==========================================================
@bed_allotment_bp.route('/history', methods=['GET', 'POST'])
def bed_history():
    db = get_db()

    ledger = (request.args.get("ledger") or request.form.get("ledger") or "").strip()
    history = []

    if ledger:
        history = get_history(db, ledger)

    return render_template("bed_history.html", history=history, ledger=ledger)


# ==========================================================
# BED HISTORY (DIRECT URL)
# URL: /bed-allotment/history/<ledger>
# Example: /bed-allotment/history/1234
# ==========================================================
@bed_allotment_bp.route('/history/<ledger>', methods=['GET'])
def bed_history_direct(ledger):
    db = get_db()
    history = get_history(db, ledger)
    return render_template("bed_history.html", history=history, ledger=ledger)
