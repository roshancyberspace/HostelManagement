from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models.db import get_db
from models.inspection_schedule_model import get_overdue_common_areas
from models.floor_model import floor_label_sql, floor_order_sql
from datetime import date

from modules.bed_allotment.service import get_beds_for_allotment, allot_bed

dashboard_bp = Blueprint("dashboard", __name__)


def ensure_dashboard_finance_tables(db):
    try:
        cur = db.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hostel_fee_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ledger_no TEXT,
                amount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'PENDING',
                paid_on TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hostel_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                category TEXT DEFAULT 'GENERAL',
                amount REAL NOT NULL DEFAULT 0,
                expense_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()
        return True
    except Exception:
        return False


# =====================================================
# ROLE CHECK
# =====================================================
def is_superintendent():
    return (
        "user" in session and
        session["user"].get("role") == "SUPERINTENDENT"
    )


# =====================================================
# ✅ AUTO ROOM STATUS UPDATE (VACANT/OCCUPIED)
# =====================================================
def update_room_status_auto(db, room_id: int):
    """
    Updates rooms.status to:
    - OCCUPIED if any bed is ALLOTTED in the room
    - VACANT if no bed allotted
    Keeps DAMAGED as it is (does not override).
    """
    cur = db.cursor()

    # Do not override DAMAGED rooms
    cur.execute("SELECT status FROM rooms WHERE id=?", (room_id,))
    row = cur.fetchone()
    if not row:
        return

    if row["status"] == "DAMAGED":
        return

    # Check if any bed allotted in this room
    cur.execute("""
        SELECT 1
        FROM beds b
        JOIN bed_allotments a
          ON a.bed_id = b.id
         AND a.status='ALLOTTED'
        WHERE b.room_id = ?
        LIMIT 1
    """, (room_id,))
    occupied = cur.fetchone() is not None

    new_status = "OCCUPIED" if occupied else "VACANT"

    cur.execute("""
        UPDATE rooms
        SET status = ?
        WHERE id = ?
    """, (new_status, room_id))


# =====================================================
# MAIN DASHBOARD
# =====================================================
@dashboard_bp.route("/")
def dashboard():
    if "user" not in session:
        return render_template("landing.html")

    db = get_db()
    cur = db.cursor()
    finance_tables_ready = ensure_dashboard_finance_tables(db)

    # ---------------- ROOMS ----------------
    cur.execute("SELECT COUNT(*) AS total_rooms FROM rooms")
    total_rooms = cur.fetchone()["total_rooms"]

    cur.execute("""
        SELECT COUNT(*) AS vacant_rooms
        FROM rooms r
        WHERE NOT EXISTS (
            SELECT 1
            FROM beds b
            JOIN bed_allotments a
              ON a.bed_id = b.id
             AND a.status = 'ALLOTTED'
            WHERE b.room_id = r.id
        )
    """)
    vacant_rooms = cur.fetchone()["vacant_rooms"]

    cur.execute("""
        SELECT COUNT(*) AS damaged_rooms
        FROM rooms
        WHERE status = 'DAMAGED'
    """)
    damaged_rooms = cur.fetchone()["damaged_rooms"]

    # ---------------- BEDS ----------------
    cur.execute("SELECT COUNT(*) AS total_beds FROM beds")
    total_beds = cur.fetchone()["total_beds"]

    cur.execute("""
        SELECT COUNT(*) AS beds_engaged
        FROM bed_allotments
        WHERE status = 'ALLOTTED'
    """)
    beds_engaged = cur.fetchone()["beds_engaged"]

    cur.execute("""
        SELECT COUNT(*) AS beds_vacant
        FROM beds b
        WHERE b.id NOT IN (
            SELECT bed_id
            FROM bed_allotments
            WHERE status='ALLOTTED'
        )
    """)
    beds_vacant = cur.fetchone()["beds_vacant"]

    capacity_left = beds_vacant

    occupancy_percent = 0.0
    if total_beds > 0:
        occupancy_percent = round((beds_engaged / total_beds) * 100, 2)

    # ---------------- STUDENTS ----------------
    cur.execute("SELECT COUNT(*) AS student_total FROM students")
    student_total = cur.fetchone()["student_total"]

    cur.execute("""
        SELECT COUNT(*) AS student_active
        FROM students
        WHERE status = 'ACTIVE'
    """)
    student_active = cur.fetchone()["student_active"]

    # ---------------- MISMATCH ----------------
    cur.execute("""
        SELECT COUNT(*) AS bed_mismatch
        FROM students
        WHERE status = 'ACTIVE'
          AND ledger_no NOT IN (
              SELECT ledger_number
              FROM bed_allotments
              WHERE status = 'ALLOTTED'
          )
    """)
    bed_mismatch = cur.fetchone()["bed_mismatch"]

    # ---------------- COMMON AREAS ----------------
    cur.execute("SELECT COUNT(*) AS total_common FROM common_areas")
    total_common = cur.fetchone()["total_common"]

    cur.execute("""
        SELECT COUNT(*) AS damaged_common
        FROM common_areas
        WHERE status = 'DAMAGED'
    """)
    damaged_common = cur.fetchone()["damaged_common"]

    # ---------------- INSPECTIONS ----------------
    overdue = get_overdue_common_areas(30)
    overdue_count = len(overdue)

    # ---------------- GATE PASS COUNTS ----------------
    pending_gate_pass = 0
    gate_pass_violations = 0

    try:
        cur.execute("""
            SELECT COUNT(*) AS pending
            FROM gate_pass
            WHERE status = 'PENDING'
        """)
        pending_gate_pass = cur.fetchone()["pending"]
    except Exception:
        pending_gate_pass = 0

    try:
        cur.execute("""
            SELECT COUNT(*) AS vio
            FROM gate_pass
            WHERE status = 'VIOLATION'
        """)
        gate_pass_violations = cur.fetchone()["vio"]
    except Exception:
        gate_pass_violations = 0

    # ---------------- FINANCE / PRESENCE SNAPSHOT ----------------
    try:
        if finance_tables_ready:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM hostel_fee_payments
                WHERE status = 'SUBMITTED'
            """)
        else:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM pocket_money_transactions
                WHERE txn_type = 'COLLECT'
            """)
        total_fee_submitted = round(cur.fetchone()["total"] or 0, 2)
    except Exception:
        total_fee_submitted = 0

    try:
        if finance_tables_ready:
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM hostel_fee_payments
                WHERE status = 'PENDING'
            """)
            fee_pending_count = cur.fetchone()["total"]
        else:
            fee_pending_count = bed_mismatch
    except Exception:
        fee_pending_count = bed_mismatch

    try:
        if finance_tables_ready:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM hostel_expenses
            """)
        else:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM pocket_money_transactions
                WHERE txn_type = 'EXPENSE'
            """)
        total_expense = round(cur.fetchone()["total"] or 0, 2)
    except Exception:
        total_expense = 0

    latest_attendance_date = None
    try:
        cur.execute("""
            SELECT attendance_date
            FROM student_attendance
            ORDER BY attendance_date DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        latest_attendance_date = row["attendance_date"] if row else None
    except Exception:
        latest_attendance_date = None

    if latest_attendance_date:
        try:
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM student_attendance
                WHERE attendance_date = ?
                  AND status = 'PRESENT'
            """, (latest_attendance_date,))
            present_in_hostel = cur.fetchone()["total"]
        except Exception:
            present_in_hostel = student_active
    else:
        present_in_hostel = student_active

    db.close()

    return render_template(
        "dashboard/dashboard.html",
        total_rooms=total_rooms,
        vacant_rooms=vacant_rooms,
        damaged_rooms=damaged_rooms,
        total_beds=total_beds,
        beds_engaged=beds_engaged,
        beds_vacant=beds_vacant,
        capacity_left=capacity_left,
        occupancy_percent=occupancy_percent,
        student_total=student_total,
        student_active=student_active,
        bed_mismatch=bed_mismatch,
        total_common=total_common,
        damaged_common=damaged_common,
        overdue_count=overdue_count,
        pending_gate_pass=pending_gate_pass,
        gate_pass_violations=gate_pass_violations,
        total_fee_submitted=total_fee_submitted,
        total_expense=total_expense,
        present_in_hostel=present_in_hostel,
        fee_pending_count=fee_pending_count,
        latest_attendance_date=latest_attendance_date or date.today().isoformat(),
        crumbs=[("Dashboard", None)]
    )


# =====================================================
# VACANT ROOMS LIST
# =====================================================
@dashboard_bp.route("/vacant-rooms")
def vacant_rooms_list():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()

    cur.execute(f"""
        SELECT
            r.id AS room_id,
            {floor_label_sql("f")} AS floor_no,
            r.room_no,
            r.room_type,
            r.status,
            COUNT(b.id) AS total_beds_in_room
        FROM rooms r
        JOIN floors f ON f.id = r.floor_id
        LEFT JOIN beds b ON b.room_id = r.id
        WHERE NOT EXISTS (
            SELECT 1
            FROM beds b2
            JOIN bed_allotments a
              ON a.bed_id = b2.id
             AND a.status = 'ALLOTTED'
            WHERE b2.room_id = r.id
        )
        GROUP BY r.id
        ORDER BY {floor_order_sql("f")}, r.room_no
    """)
    rooms = cur.fetchall()

    db.close()

    return render_template(
        "dashboard/vacant_rooms.html",
        rooms=rooms,
        crumbs=[
            ("Dashboard", "/"),
            ("Vacant Rooms", None)
        ]
    )


# =====================================================
# ROOM DETAILS + BEDS + OCCUPANCY %
# =====================================================
@dashboard_bp.route("/vacant-room/<int:room_id>")
def vacant_room_detail(room_id):
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()

    # ✅ Auto-update room status
    try:
        update_room_status_auto(db, room_id)
        db.commit()
    except Exception:
        db.rollback()

    cur = db.cursor()

    cur.execute(f"""
        SELECT
            r.id,
            r.room_no,
            r.room_type,
            r.status,
            {floor_label_sql("f")} AS floor_no
        FROM rooms r
        JOIN floors f ON f.id = r.floor_id
        WHERE r.id = ?
    """, (room_id,))
    room = cur.fetchone()

    if not room:
        db.close()
        flash("Room not found", "danger")
        return redirect(url_for("dashboard.vacant_rooms_list"))

    cur.execute("""
        SELECT
            b.id AS bed_id,
            b.bed_no,
            CASE
                WHEN a.id IS NULL THEN 'VACANT'
                ELSE 'ALLOTTED'
            END AS bed_status,
            a.ledger_number,
            s.student_name,
            s.class,
            s.section,
            a.allot_date
        FROM beds b
        LEFT JOIN bed_allotments a
               ON a.bed_id = b.id AND a.status = 'ALLOTTED'
        LEFT JOIN students s
               ON s.ledger_no = a.ledger_number
        WHERE b.room_id = ?
        ORDER BY b.bed_no
    """, (room_id,))
    beds = cur.fetchall()

    total_beds = len(beds)
    engaged_beds = len([x for x in beds if x["bed_status"] == "ALLOTTED"])
    vacant_beds = total_beds - engaged_beds

    occupancy_percent = 0.0
    if total_beds > 0:
        occupancy_percent = round((engaged_beds / total_beds) * 100, 2)

    existing_bed_nos = set([b["bed_no"] for b in beds])
    standard = ["B1", "B2", "B3"]
    missing_beds = [x for x in standard if x not in existing_bed_nos]
    extra_beds = [b for b in beds if b["bed_no"] not in standard]

    db.close()

    return render_template(
        "dashboard/vacant_room_detail.html",
        room=room,
        beds=beds,
        total_beds=total_beds,
        engaged_beds=engaged_beds,
        vacant_beds=vacant_beds,
        occupancy_percent=occupancy_percent,
        missing_beds=missing_beds,
        extra_beds=extra_beds,
        is_superintendent=is_superintendent(),
        crumbs=[
            ("Dashboard", "/"),
            ("Vacant Rooms", "/vacant-rooms"),
            (f"Room {room['room_no']}", None)
        ]
    )


# =====================================================
# ✅ CREATE BEDS CUSTOM (2/3/4)
# =====================================================
@dashboard_bp.route("/vacant-room/<int:room_id>/create-beds-custom", methods=["POST"])
def create_beds_custom(room_id):
    if not is_superintendent():
        flash("Unauthorized: Only Superintendent can create beds.", "danger")
        return redirect(url_for("dashboard.vacant_room_detail", room_id=room_id))

    count = int(request.form.get("bed_count") or 3)
    if count not in (2, 3, 4):
        count = 3

    wanted = [f"B{i}" for i in range(1, count + 1)]

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id FROM rooms WHERE id=?", (room_id,))
    room = cur.fetchone()
    if not room:
        db.close()
        flash("Room not found", "danger")
        return redirect(url_for("dashboard.vacant_rooms_list"))

    cur.execute("SELECT bed_no FROM beds WHERE room_id=?", (room_id,))
    existing = set([r["bed_no"] for r in cur.fetchall()])

    created = 0
    try:
        for bed_no in wanted:
            if bed_no not in existing:
                cur.execute("""
                    INSERT INTO beds (room_id, bed_no, status)
                    VALUES (?, ?, 'VACANT')
                """, (room_id, bed_no))
                created += 1

        db.commit()
        if created == 0:
            flash(f"✅ Beds already exist for {count} count. Nothing created.", "info")
        else:
            flash(f"✅ Created {created} bed(s): {', '.join([x for x in wanted if x not in existing])}", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error creating beds: {str(e)}", "danger")
    finally:
        db.close()

    return redirect(url_for("dashboard.vacant_room_detail", room_id=room_id))


# =====================================================
# ✅ RE-NUMBER BEDS TO B1,B2,B3 + DELETE EXTRAS (SAFE)
# =====================================================
@dashboard_bp.route("/vacant-room/<int:room_id>/renumber-beds", methods=["POST"])
def renumber_beds(room_id):
    if not is_superintendent():
        flash("Unauthorized: Only Superintendent can renumber beds.", "danger")
        return redirect(url_for("dashboard.vacant_room_detail", room_id=room_id))

    db = get_db()
    cur = db.cursor()

    try:
        # Get beds in room ordered by id (stable order)
        cur.execute("""
            SELECT id, bed_no
            FROM beds
            WHERE room_id=?
            ORDER BY id
        """, (room_id,))
        all_beds = cur.fetchall()

        if not all_beds:
            flash("No beds found in this room.", "danger")
            db.close()
            return redirect(url_for("dashboard.vacant_room_detail", room_id=room_id))

        # ✅ Check if any bed is currently allotted (allotted ones cannot be renamed or deleted)
        cur.execute("""
            SELECT b.id, b.bed_no
            FROM beds b
            JOIN bed_allotments a
              ON a.bed_id = b.id
             AND a.status='ALLOTTED'
            WHERE b.room_id=?
        """, (room_id,))
        allotted = cur.fetchall()

        if allotted:
            flash("⚠️ Cannot renumber because some beds are ALLOTTED in this room. Vacate first.", "danger")
            db.close()
            return redirect(url_for("dashboard.vacant_room_detail", room_id=room_id))

        # ✅ Strategy:
        # Keep first 3 beds, rename to B1,B2,B3
        # Delete remaining beds safely
        keep = all_beds[:3]
        remove = all_beds[3:]

        # Rename keep beds
        target_names = ["B1", "B2", "B3"]
        for i, bed in enumerate(keep):
            cur.execute("""
                UPDATE beds
                SET bed_no = ?, status='VACANT'
                WHERE id=?
            """, (target_names[i], bed["id"]))

        # Delete extras
        deleted = 0
        for bed in remove:
            cur.execute("DELETE FROM beds WHERE id=?", (bed["id"],))
            deleted += 1

        db.commit()
        flash(f"✅ Renumbered beds to B1,B2,B3 and deleted {deleted} extra bed(s).", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error renumbering beds: {str(e)}", "danger")
    finally:
        db.close()

    return redirect(url_for("dashboard.vacant_room_detail", room_id=room_id))


# =====================================================
# MISMATCH LIST
# =====================================================
@dashboard_bp.route("/mismatch-active-without-bed", methods=["GET"])
def mismatch_active_without_bed():
    if "user" not in session or session["user"]["role"] != "SUPERINTENDENT":
        return "Access Denied", 403

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT ledger_no, student_name, class, section
        FROM students
        WHERE status = 'ACTIVE'
          AND ledger_no NOT IN (
              SELECT ledger_number
              FROM bed_allotments
              WHERE status = 'ALLOTTED'
          )
        ORDER BY class, section, student_name
    """)
    students = cur.fetchall()

    beds = get_beds_for_allotment(db)

    db.close()

    return render_template(
        "dashboard/bed_mismatch.html",
        students=students,
        beds=beds,
        crumbs=[
            ("Dashboard", "/"),
            ("Bed Allocation Mismatch", None)
        ]
    )


# =====================================================
# ONE-CLICK BED ALLOT ACTION
# =====================================================
@dashboard_bp.route("/mismatch-allot-bed", methods=["POST"])
def mismatch_allot_bed():
    if "user" not in session or session["user"]["role"] != "SUPERINTENDENT":
        return "Access Denied", 403

    ledger_no = (request.form.get("ledger_no") or "").strip()
    bed_id = request.form.get("bed_id")

    if not ledger_no or not bed_id:
        flash("Ledger and Bed selection required", "danger")
        return redirect(url_for("dashboard.mismatch_active_without_bed"))

    db = get_db()
    try:
        allot_bed(db, ledger_no, int(bed_id))
        db.commit()
        flash(f"✅ Bed allotted to Ledger {ledger_no}", "success")
    except Exception as e:
        db.rollback()
        flash(str(e), "danger")
    finally:
        db.close()

    return redirect(url_for("dashboard.mismatch_active_without_bed"))


# =====================================================
# INSPECTION ALERTS
# =====================================================
@dashboard_bp.route("/inspection-alerts")
def inspection_alerts():
    due = get_overdue_common_areas(30)

    return render_template(
        "dashboard/inspection_alerts.html",
        due=due,
        crumbs=[
            ("Dashboard", "/"),
            ("Inspection Alerts", None)
        ]
    )


# =====================================================
# SYSTEM CHECK
# =====================================================
@dashboard_bp.route("/system-check")
def system_check():
    if "user" not in session or session["user"]["role"] != "SUPERINTENDENT":
        return "Access Denied", 403

    return render_template("system_check.html")
