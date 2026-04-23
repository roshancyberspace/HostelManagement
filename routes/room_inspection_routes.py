from flask import Blueprint, flash, redirect, render_template, request, url_for

from models.db import get_db
from models.room_inspection_model import (
    get_ac_student_rooms,
    get_inspection_master_items,
    get_latest_room_issues,
    get_room_expected_items,
    save_room_inspection,
)


room_inspection_bp = Blueprint("room_inspection", __name__, url_prefix="/room-inspection")


@room_inspection_bp.route("/", methods=["GET"])
def inspection_dashboard():
    db = get_db()
    issues = get_latest_room_issues(db, 300)
    condition = (request.args.get("condition") or "").strip().upper()
    search = (request.args.get("search") or "").strip().lower()

    if condition:
        issues = [row for row in issues if (row["condition"] or "").upper() == condition]

    if search:
        issues = [
            row
            for row in issues
            if search in (row["room_no"] or "").lower()
            or search in (row["item_name"] or "").lower()
            or search in (row["floor_name"] or "").lower()
            or search in (row["inspector_name"] or "").lower()
            or search in (row["remarks"] or "").lower()
        ]

    damaged_count = sum(1 for row in issues if (row["condition"] or "").upper() == "DAMAGED")
    missing_count = sum(1 for row in issues if (row["condition"] or "").upper() == "MISSING")

    return render_template(
        "inspection/room_reports.html",
        issues=issues,
        condition=condition,
        search=search,
        damaged_count=damaged_count,
        missing_count=missing_count,
    )


@room_inspection_bp.route("/entry", methods=["GET", "POST"])
def room_entry():
    db = get_db()
    rooms = get_ac_student_rooms(db)
    items = get_inspection_master_items(db)
    selected_room_id = request.args.get("room_id") or request.form.get("room_id")

    expected_map = {}
    selected_room = None
    if selected_room_id:
        expected_items = get_room_expected_items(db, selected_room_id)
        expected_map = {x["item_name"]: x["qty"] for x in expected_items}
        selected_room = next((r for r in rooms if str(r["id"]) == str(selected_room_id)), None)

    if request.method == "POST":
        room_id = request.form.get("room_id")
        inspector = request.form.get("inspector_name", "").strip()
        remarks = request.form.get("remarks", "").strip()

        if not room_id:
            flash("Please select a room.", "danger")
            return redirect(url_for("room_inspection.room_entry"))

        item_results = []
        for it in items:
            item_id = it["id"]
            item_results.append(
                {
                    "item_id": item_id,
                    "condition": request.form.get(f"condition_{item_id}", "GOOD"),
                    "remarks": request.form.get(f"remarks_{item_id}", ""),
                }
            )

        try:
            save_room_inspection(db, room_id, inspector, remarks, item_results)
            flash("Room inspection saved successfully.", "success")
            return redirect(url_for("room_inspection.room_entry", room_id=room_id))
        except Exception as e:
            flash(str(e), "danger")
            return redirect(url_for("room_inspection.room_entry", room_id=room_id))

    return render_template(
        "inspection/room_entry.html",
        rooms=rooms,
        items=items,
        expected_map=expected_map,
        selected_room_id=selected_room_id,
        selected_room=selected_room,
    )
