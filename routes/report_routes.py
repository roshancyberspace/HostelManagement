from flask import Blueprint, render_template, request

from models.floor_model import get_floors
from models.hostel_model import get_hostels
from models.room_model import get_rooms
from services.report_service import (
    get_floor_heatmap,
    get_floor_report,
    get_hostel_report,
    get_room_report,
)

report_bp = Blueprint("reports", __name__, url_prefix="/reports")


@report_bp.route("/rooms")
def room_selector():
    search = (request.args.get("search") or "").strip().lower()
    status = (request.args.get("status") or "").strip().upper()
    ac_type = (request.args.get("ac_type") or "").strip().upper()

    rooms = get_rooms()
    if search:
        rooms = [
            room
            for room in rooms
            if search in (room["room_no"] or "").lower()
            or search in (room["floor_no"] or "").lower()
            or search in (room["block_name"] or "").lower()
            or search in (room["hostel_name"] or "").lower()
        ]
    if status:
        rooms = [room for room in rooms if (room["status"] or "").upper() == status]
    if ac_type:
        rooms = [room for room in rooms if (room["ac_type"] or "").upper() == ac_type]

    return render_template(
        "reports/room_selector.html",
        rooms=rooms,
        search=search,
        status=status,
        ac_type=ac_type,
        crumbs=[("Reports", None), ("Rooms", None)],
    )


@report_bp.route("/room/<int:room_id>")
def room_report(room_id):
    return render_template(
        "reports/room_report.html",
        data=get_room_report(room_id),
        crumbs=[("Reports", "/reports/rooms"), ("Room Report", None)],
    )


@report_bp.route("/floors")
def floor_selector():
    search = (request.args.get("search") or "").strip().lower()
    floors = get_floors()
    if search:
        floors = [
            floor
            for floor in floors
            if search in (floor["floor_no"] or "").lower()
            or search in (floor["block_name"] or "").lower()
            or search in (floor["hostel_name"] or "").lower()
        ]

    return render_template(
        "reports/floor_selector.html",
        floors=floors,
        search=search,
        crumbs=[("Reports", None), ("Floors", None)],
    )


@report_bp.route("/floor/<int:floor_id>")
def floor_report(floor_id):
    return render_template(
        "reports/floor_report.html",
        data=get_floor_report(floor_id),
        floor_id=floor_id,
        crumbs=[("Reports", "/reports/floors"), ("Floor Report", None)],
    )


@report_bp.route("/hostel")
def hostel_report():
    return render_template(
        "reports/hostel_report.html",
        data=get_hostel_report(),
        crumbs=[("Reports", None), ("Hostel Summary", None)],
    )


@report_bp.route("/floor-heatmap")
def floor_heatmap():
    hostel_id = request.args.get("hostel_id", type=int)
    return render_template(
        "reports/floor_heatmap.html",
        heatmap=get_floor_heatmap(hostel_id=hostel_id),
        hostels=get_hostels(),
        selected_hostel_id=hostel_id,
        crumbs=[("Reports", None), ("Floor Heatmap", None)],
    )
