from flask import (
    Blueprint, render_template, request,
    jsonify, redirect, url_for, flash, session
)
from services import structure_service
from services.rbac import has_permission
from models import (
    hostel_model,
    block_model,
    floor_model,
    room_model,
    bed_model,
    common_area_model,
    room_item_model
)
from models.db import get_db

structure_bp = Blueprint("structure", __name__, url_prefix="/structure")


def require_superintendent():
    if not has_permission("hostel_structure.manage"):
        raise Exception("Only Hostel Superintendent can modify structure")


@structure_bp.route("/hostel", methods=["GET", "POST"])
def hostel():
    if request.method == "POST":
        try:
            require_superintendent()
            structure_service.create_hostel(request.form["name"])
            flash("Hostel created successfully", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("structure.hostel"))

    return render_template(
        "structure/hostel.html",
        hostels=hostel_model.get_hostels(),
        can_delete=hostel_model.can_delete_hostel,
        crumbs=[("Hostel", None)]
    )


@structure_bp.route("/hostel/delete/<int:id>", methods=["POST"])
def delete_hostel(id):
    try:
        require_superintendent()
        hostel_model.delete_hostel(id)
        flash("Hostel deleted", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("structure.hostel"))


@structure_bp.route("/block", methods=["GET", "POST"])
def block():
    if request.method == "POST":
        try:
            require_superintendent()
            structure_service.create_block(
                request.form["hostel_id"],
                request.form["name"]
            )
            flash("Block created", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("structure.block"))

    return render_template(
        "structure/block.html",
        hostels=hostel_model.get_hostels(),
        blocks=block_model.get_blocks(),
        can_delete=block_model.can_delete_block,
        crumbs=[("Hostel", "/structure/hostel"), ("Block", None)]
    )


@structure_bp.route("/block/delete/<int:id>", methods=["POST"])
def delete_block(id):
    try:
        require_superintendent()
        block_model.delete_block(id)
        flash("Block deleted", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("structure.block"))


@structure_bp.route("/floor", methods=["GET", "POST"])
def floor():
    if request.method == "POST":
        try:
            require_superintendent()
            structure_service.create_floor(
                request.form["block_id"],
                request.form["floor_no"]
            )
            flash("Floor created", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("structure.floor"))

    return render_template(
        "structure/floor.html",
        blocks=block_model.get_blocks(),
        floors=floor_model.get_floors(),
        can_delete=floor_model.can_delete_floor,
        crumbs=[
            ("Hostel", "/structure/hostel"),
            ("Block", "/structure/block"),
            ("Floor", None)
        ]
    )


@structure_bp.route("/floor/delete/<int:id>", methods=["POST"])
def delete_floor(id):
    try:
        require_superintendent()
        floor_model.delete_floor(id)
        flash("Floor deleted", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("structure.floor"))


@structure_bp.route("/room", methods=["GET", "POST"])
def room():
    if request.method == "POST":
        try:
            require_superintendent()
            structure_service.create_room(
                floor_id=request.form["floor_id"],
                room_no=request.form["room_no"],
                ac_type=request.form.get("ac_type", "NON_AC")
            )
            flash("Room created", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("structure.room"))

    return render_template(
        "structure/room.html",
        floors=floor_model.get_floors(),
        rooms=room_model.get_rooms(),
        can_delete=room_model.can_delete_room,
        crumbs=[
            ("Hostel", "/structure/hostel"),
            ("Block", "/structure/block"),
            ("Floor", "/structure/floor"),
            ("Room", None)
        ]
    )


@structure_bp.route("/room/delete/<int:id>", methods=["POST"])
def delete_room(id):
    try:
        require_superintendent()
        room_model.delete_room(id)
        flash("Room deleted", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("structure.room"))


@structure_bp.route("/room/toggle-ac/<int:id>", methods=["POST"])
def toggle_room_ac(id):
    try:
        require_superintendent()
        room_model.toggle_ac(id)
        flash("AC type updated", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("structure.room"))


@structure_bp.route("/bed", methods=["GET", "POST"])
def bed():
    if request.method == "POST":
        try:
            require_superintendent()
            structure_service.create_bed(
                request.form["room_id"],
                request.form["bed_no"]
            )
            flash("Bed added", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("structure.bed"))

    return render_template(
        "structure/bed.html",
        hostels=hostel_model.get_hostels(),
        beds=bed_model.get_all_beds(),
        crumbs=[
            ("Hostel", "/structure/hostel"),
            ("Block", "/structure/block"),
            ("Floor", "/structure/floor"),
            ("Room", "/structure/room"),
            ("Bed", None)
        ]
    )


@structure_bp.route("/bed/delete/<int:id>", methods=["POST"])
def delete_bed(id):
    try:
        require_superintendent()
        bed_model.delete_bed(id)
        flash("Bed deleted", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("structure.bed"))


@structure_bp.route("/common-area", methods=["GET", "POST"])
def common_area():
    if request.method == "POST":
        try:
            require_superintendent()
            structure_service.create_common_area(
                request.form["floor_id"],
                request.form["name"]
            )
            flash("Common area created", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("structure.common_area"))

    return render_template(
        "structure/common_area.html",
        floors=floor_model.get_floors(),
        areas=common_area_model.get_common_areas(),
        crumbs=[
            ("Hostel", "/structure/hostel"),
            ("Block", "/structure/block"),
            ("Floor", "/structure/floor"),
            ("Common Area", None)
        ]
    )


@structure_bp.route("/common-area/delete/<int:id>", methods=["POST"])
def delete_common_area(id):
    try:
        require_superintendent()
        common_area_model.delete_common_area(id)
        flash("Common area deleted", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("structure.common_area"))


@structure_bp.route("/room-items/<int:room_id>", methods=["GET", "POST"])
def room_items(room_id):
    if request.method == "POST":
        try:
            require_superintendent()
            room_item_model.add_item(
                room_id,
                request.form["item_name"],
                request.form.get("quantity", 1)
            )
            flash("Item added", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("structure.room_items", room_id=room_id))

    return render_template(
        "structure/room_items.html",
        room_id=room_id,
        items=room_item_model.get_items_by_room(room_id),
        crumbs=[
            ("Hostel", "/structure/hostel"),
            ("Room", "/structure/room"),
            ("Room Items", None)
        ]
    )


@structure_bp.route("/room-items/delete/<int:item_id>", methods=["POST"])
def delete_room_item(item_id):
    try:
        require_superintendent()
        room_item_model.delete_item(item_id)
        flash("Item deleted", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(request.referrer or url_for("structure.room"))


@structure_bp.route("/api/blocks/<int:hostel_id>")
def api_blocks(hostel_id):
    rows = get_db().execute(
        "SELECT id, name FROM blocks WHERE hostel_id=? ORDER BY name",
        (hostel_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@structure_bp.route("/api/floors/<int:block_id>")
def api_floors(block_id):
    rows = floor_model.get_floors_for_block(block_id)
    return jsonify([dict(r) for r in rows])


@structure_bp.route("/api/rooms/<int:floor_id>")
def api_rooms(floor_id):
    rows = get_db().execute(
        "SELECT id, room_no FROM rooms WHERE floor_id=? ORDER BY room_no",
        (floor_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])
