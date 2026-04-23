from flask import render_template, request, redirect, url_for, flash, session, jsonify
from services.rbac import has_permission
from . import laundry_register_bp
from .services import (
    get_all_records,
    issue_laundry,
    mark_return,
    get_student_by_ledger
)


def superintendent_only():
    return has_permission("laundry.manage")


# ---------- API FOR AUTO-FILL ----------
@laundry_register_bp.route("/api/student/<ledger_no>")
def api_student_lookup(ledger_no):
    student = get_student_by_ledger(ledger_no)
    if not student:
        return jsonify({"error": "Not found"}), 404
    if student.get("student_photo"):
        if student["student_photo"].startswith("instance_uploads/"):
            student["photo_url"] = url_for(
                "student_master.student_media",
                filename=student["student_photo"].replace("instance_uploads/", "", 1)
            )
        else:
            student["photo_url"] = url_for("static", filename=student["student_photo"])
    else:
        student["photo_url"] = ""
    return jsonify(student)


# ---------- UI ----------
@laundry_register_bp.route("/", methods=["GET", "POST"])
def index():
    if not superintendent_only():
        flash("Unauthorized", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        try:
            issue_laundry(request.form, request.files)
            flash("Laundry issued successfully", "success")
        except Exception as e:
            flash(str(e), "danger")

    search = (request.args.get("search") or "").strip()
    status = (request.args.get("status") or "ALL").upper()

    records = get_all_records()
    if search:
        needle = search.lower()
        records = [
            row for row in records
            if needle in str(row["ledger_no"]).lower()
            or needle in (row["student_name"] or "").lower()
            or needle in (row["class_section"] or "").lower()
            or needle in (row["items_given"] or "").lower()
        ]

    if status != "ALL":
        records = [row for row in records if (row["status"] or "").upper() == status]

    total_count = len(records)
    pending_count = sum(1 for row in records if (row["status"] or "").upper() != "RETURNED")
    returned_count = sum(1 for row in records if (row["status"] or "").upper() == "RETURNED")

    return render_template(
        "laundry_register/index.html",
        records=records,
        search=search,
        status=status,
        total_count=total_count,
        pending_count=pending_count,
        returned_count=returned_count,
    )


@laundry_register_bp.route("/return/<int:record_id>", methods=["POST"])
def return_laundry(record_id):
    if not superintendent_only():
        flash("Unauthorized", "danger")
        return redirect(url_for("dashboard"))

    try:
        mark_return(record_id, request.form, request.files)
        flash("Laundry returned successfully", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("laundry_register.index"))
