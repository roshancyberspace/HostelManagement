from models import (
    hostel_model, block_model, floor_model,
    room_model, common_area_model
)
from models.room_item_model import add_item

# ================= HOSTEL =================
def create_hostel(name):
    hostel_model.add_hostel(name)

def create_block(hostel_id, name):
    block_model.add_block(hostel_id, name)

def create_floor(block_id, floor_no):
    floor_model.add_floor(block_id, floor_no)

# ================= ROOM (AUTO ITEMS) =================
def create_room(floor_id, room_no, ac_type="NON_AC"):
    room_model.add_room(floor_id, room_no, ac_type)

    # Auto standard items
    standard_items = [
        ("Bed", 1),
        ("Fan", 1),
        ("Light", 2),
        ("Switch Board", 1),
        ("Study Table", 1)
    ]

    if ac_type == "AC":
        standard_items.append(("AC Unit", 1))

    # Get last inserted room
    from models.db import get_db
    room_id = get_db().execute(
        "SELECT id FROM rooms ORDER BY id DESC LIMIT 1"
    ).fetchone()["id"]

    for item, qty in standard_items:
        add_item(room_id, item, qty)

def create_common_area(floor_id, name):
    common_area_model.add_common_area(floor_id, name)

def create_bed(room_id, bed_no):
    from models.bed_model import add_bed
    add_bed(room_id, bed_no)
