from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import common_area_model, hostel_model, room_model
from models.inspection_model import get_pre_post
from models.recovery_model import get_recoveries
from models.room_item_model import get_items_by_room, update_status as update_item
from services.inspection_service import inspect_common, inspect_room


inspection_bp = Blueprint("inspection", __name__, url_prefix="/inspection")


@inspection_bp.route("/room", methods=["GET", "POST"])
def room_inspection():
    selected_room_id = request.args.get("room_id")
    rooms = room_model.get_rooms()
    room_items = []
    selected_room = None

    if selected_room_id:
        room_items = get_items_by_room(selected_room_id)
        selected_room = next((r for r in rooms if str(r["id"]) == str(selected_room_id)), None)

    if request.method == "POST":
        room_id = request.form.get("room_id")
        inspection_type = request.form.get("inspection_type")

        if room_id and inspection_type:
            inspect_room(
                room_id=room_id,
                insp_type=inspection_type,
                remarks=request.form.get("remarks", ""),
                damage=request.form.get("damage", ""),
                fine=request.form.get("fine", 0),
            )

            for key in request.form:
                if key.startswith("item_"):
                    item_id = key.replace("item_", "")
                    status = request.form.get(key)
                    remarks = request.form.get(f"remark_{item_id}", "")

                    if status:
                        update_item(item_id=item_id, status=status, remarks=remarks)

            flash("Room inspection saved successfully.", "success")
            return redirect(url_for("inspection.room_inspection", room_id=room_id))

        flash("Please select a room and inspection type.", "danger")
        return redirect(url_for("inspection.room_inspection"))

    return render_template(
        "inspection/room_inspection.html",
        hostels=hostel_model.get_hostels(),
        rooms=rooms,
        items=room_items,
        selected_room_id=selected_room_id,
        selected_room=selected_room,
        crumbs=[("Inspection", None), ("Room Inspection", None)],
    )


@inspection_bp.route("/common", methods=["GET", "POST"])
def common_inspection():
    areas = common_area_model.get_common_areas()
    selected_area_id = request.args.get("area_id")

    if request.method == "POST":
        area_id = request.form.get("area_id")
        inspection_type = request.form.get("inspection_type")

        if area_id and inspection_type:
            inspect_common(
                common_area_id=area_id,
                insp_type=inspection_type,
                remarks=request.form.get("remarks", ""),
                damage=request.form.get("damage", ""),
                fine=request.form.get("fine", 0),
            )
            flash("Common area inspection saved successfully.", "success")
            return redirect(url_for("inspection.common_inspection", area_id=area_id))

        flash("Please select a common area and inspection type.", "danger")
        return redirect(url_for("inspection.common_inspection"))

    return render_template(
        "inspection/common_inspection.html",
        hostels=hostel_model.get_hostels(),
        areas=areas,
        selected_area_id=selected_area_id,
        crumbs=[("Inspection", None), ("Common Area Inspection", None)],
    )


@inspection_bp.route("/recovery-ledger")
def recovery_ledger():
    target_type = (request.args.get("type") or "").strip().upper()
    search = (request.args.get("search") or "").strip()

    return render_template(
        "inspection/recovery_ledger.html",
        records=get_recoveries(target_type=target_type, search=search),
        target_type=target_type,
        search=search,
        crumbs=[("Inspection", None), ("Recovery Ledger", None)],
    )


@inspection_bp.route("/compare/<target_type>/<int:target_id>")
def inspection_compare(target_type, target_id):
    pre, post = get_pre_post(target_type=target_type.upper(), target_id=target_id)

    return render_template(
        "inspection/compare.html",
        pre=pre,
        post=post,
        target_type=target_type.upper(),
        target_id=target_id,
        crumbs=[("Inspection", None), ("Comparison", None)],
    )
