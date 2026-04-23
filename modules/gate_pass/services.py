from models.db import get_db
from datetime import datetime
from modules.student_profile.services import (
    auto_behaviour_from_gatepass,
    get_student
)
from services.notification_service import notify_parent

# 🔒 POCKET MONEY CHECK (SAFE HOOK)
from modules.pocket_money.services import (
    is_wallet_clear_for_gatepass,
    get_wallet_block_reason,
    get_wallet
)


# ==============================
# GENERATE GATE PASS NUMBER
# ==============================
def generate_gate_pass_no():
    db = get_db()
    cur = db.execute("SELECT COUNT(*) c FROM gate_passes")
    count = cur.fetchone()["c"] + 1
    db.close()
    return f"GP-{count:05d}"


# ==============================
# CREATE GATE PASS (WITH CHECK)
# ==============================
def create_gate_pass(data, created_by):
    student = get_student(data["ledger_no"])
    if not student:
        raise Exception("Student record not found for this ledger number.")

    if data["expected_return_datetime"] <= data["out_datetime"]:
        raise Exception("Expected return must be after out date and time.")

    db = get_db()

    # 🔐 POCKET MONEY VALIDATION (CORRECT)
    if not is_wallet_clear_for_gatepass(data["ledger_no"]):
        reason = get_wallet_block_reason(data["ledger_no"])
        raise Exception(reason)

    gp_no = generate_gate_pass_no()

    db.execute("""
        INSERT INTO gate_passes
        (gate_pass_no, ledger_no, purpose, relation,
         out_datetime, expected_return_datetime,
         status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
    """, (
        gp_no,
        data["ledger_no"],
        data["purpose"],
        data.get("relation"),
        data["out_datetime"],
        data["expected_return_datetime"],
        datetime.now().isoformat()
    ))
    db.commit()
    notify_parent(
        data["ledger_no"],
        f"Gate Pass requested for {student['full_name']}."
    )


# ==============================
# FETCH ALL GATE PASSES
# ==============================
def get_all_gate_passes():
    db = get_db()
    rows = db.execute("""
        SELECT
            gp.*,
            s.student_name AS student_name,
            s.class AS student_class,
            s.section AS student_section
        FROM gate_passes gp
        LEFT JOIN students s ON s.ledger_no = gp.ledger_no
        ORDER BY gp.created_at DESC
    """).fetchall()
    db.close()

    enriched = []
    for row in rows:
        item = dict(row)
        wallet = get_wallet(item["ledger_no"])
        balance = wallet["current_balance"] if wallet else 0
        item["wallet"] = {
            "balance": balance,
            "low": not is_wallet_clear_for_gatepass(item["ledger_no"])
        }
        enriched.append(item)

    return enriched


# ==============================
# FETCH SINGLE GATE PASS
# ==============================
def get_gate_pass(gp_id):
    db = get_db()
    row = db.execute("""
        SELECT * FROM gate_passes WHERE id = ?
    """, (gp_id,)).fetchone()
    db.close()
    return row


# ==============================
# UPDATE STATUS (APPROVE)
# ==============================
def update_status(gp_id, status, user, override_reason=None):
    db = get_db()
    gp = get_gate_pass(gp_id)

    if not gp:
        raise Exception("Gate pass not found.")

    # 🔐 Re-check pocket money on approval
    if status == "APPROVED":
        if not is_wallet_clear_for_gatepass(gp["ledger_no"]) and not override_reason:
            raise Exception(
                "Low pocket balance. Superintendent override reason required."
            )

    cur = db.cursor()
    cur.execute("PRAGMA table_info(gate_passes)")
    columns = {row["name"] for row in cur.fetchall()}

    if "override_reason" in columns:
        db.execute("""
            UPDATE gate_passes
            SET status = ?, approved_by = ?, override_reason = ?
            WHERE id = ?
        """, (status, user, override_reason, gp_id))
    else:
        db.execute("""
            UPDATE gate_passes
            SET status = ?, approved_by = ?
            WHERE id = ?
        """, (status, user, gp_id))
    db.commit()

    student = get_student(gp["ledger_no"])

    if status == "APPROVED":
        auto_behaviour_from_gatepass(
            gp["ledger_no"],
            "APPROVED",
            user
        )
        notify_parent(
            gp["ledger_no"],
            f"Gate Pass APPROVED for {student['full_name']}."
        )


# ==============================
# MARK RETURN / VIOLATION
# ==============================
def mark_return(gp_id, is_violation, user):
    status = "VIOLATION" if is_violation else "RETURNED"
    db = get_db()

    db.execute("""
        UPDATE gate_passes
        SET actual_return_datetime = ?, status = ?
        WHERE id = ?
    """, (
        datetime.now().isoformat(),
        status,
        gp_id
    ))
    db.commit()

    gp = get_gate_pass(gp_id)
    if not gp:
        return
    student = get_student(gp["ledger_no"])

    if is_violation:
        auto_behaviour_from_gatepass(
            gp["ledger_no"],
            "VIOLATION",
            user
        )
        notify_parent(
            gp["ledger_no"],
            f"⚠️ Gate Pass VIOLATION by {student['full_name']}. Please contact hostel."
        )
    else:
        notify_parent(
            gp["ledger_no"],
            f"{student['full_name']} has returned safely to hostel."
        )


def get_gate_pass_context(gp_id):
    gp = get_gate_pass(gp_id)
    if not gp:
        return None

    student = get_student(gp["ledger_no"])
    wallet = get_wallet(gp["ledger_no"])
    balance = wallet["current_balance"] if wallet else 0

    return {
        "gp": gp,
        "student": student,
        "wallet": {
            "balance": balance,
            "low": not is_wallet_clear_for_gatepass(gp["ledger_no"]),
            "current_balance": balance,
        }
    }
