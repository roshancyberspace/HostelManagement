from datetime import date
from models.room_inspection_model import (
    create_inspection,
    add_inspection_item
)

def inspect_room_items(room_id, insp_type, items, remarks):
    insp_id = create_inspection(
        room_id,
        insp_type,
        remarks,
        date.today()
    )

    for item_id, data in items.items():
        add_inspection_item(
            insp_id,
            item_id,
            data["condition"],
            data.get("remarks", "")
        )
