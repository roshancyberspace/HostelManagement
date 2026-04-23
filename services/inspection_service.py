from datetime import date
from models.inspection_model import add_inspection
from models.room_model import update_status as update_room
from models.common_area_model import update_status as update_area
from models.recovery_model import add_recovery


# =====================================================
# ROOM INSPECTION (ROOM NUMBER WISE)
# =====================================================
def inspect_room(room_id, insp_type, remarks, damage, fine):
    """
    insp_type : PRE | POST | ROUTINE
    target    : ROOM (room number wise)
    """

    add_inspection(
        target_type="ROOM",
        target_id=room_id,
        insp_type=insp_type,
        remarks=remarks,
        damage=damage,
        fine=fine,
        date=date.today()
    )

    # Status & recovery ONLY on POST inspection
    if insp_type == "POST":
        if damage:
            update_room(room_id, "DAMAGED")

            if int(fine) > 0:
                add_recovery(
                    target_type="ROOM",
                    target_id=room_id,
                    amount=fine,
                    reason=damage
                )
        else:
            update_room(room_id, "GOOD")


# =====================================================
# COMMON AREA INSPECTION (FLOOR WISE)
# =====================================================
def inspect_common(common_area_id, insp_type, remarks, damage, fine):
    """
    insp_type : ROUTINE | SPECIAL | POST
    target    : COMMON (floor-wise via common area)
    """

    add_inspection(
        target_type="COMMON",
        target_id=common_area_id,   # 🔒 Floor-attached common area
        insp_type=insp_type,
        remarks=remarks,
        damage=damage,
        fine=fine,
        date=date.today()
    )

    # Status & recovery ONLY on POST / SPECIAL inspection
    if insp_type in ("POST", "SPECIAL"):
        if damage:
            update_area(common_area_id, "DAMAGED")

            if int(fine) > 0:
                add_recovery(
                    target_type="COMMON",
                    target_id=common_area_id,
                    amount=fine,
                    reason=damage
                )
        else:
            update_area(common_area_id, "GOOD")
