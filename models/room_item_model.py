from datetime import date
from models.db import get_db

# =====================================================
# ADD ITEM TO ROOM
# =====================================================
def add_item(room_id, item_name, quantity=1):
    db = get_db()
    db.execute("""
        INSERT INTO room_items
        (room_id, item_name, quantity, status, last_updated)
        VALUES (?, ?, ?, 'PRESENT', ?)
    """, (room_id, item_name, quantity, date.today()))
    db.commit()


# =====================================================
# UPDATE ITEM STATUS (INSPECTION / MAINTENANCE)
# =====================================================
def update_status(item_id, status, remarks=""):
    db = get_db()
    db.execute("""
        UPDATE room_items
        SET status = ?, remarks = ?, last_updated = ?
        WHERE id = ?
    """, (status, remarks, date.today(), item_id))
    db.commit()


# =====================================================
# GET ITEMS BY ROOM
# =====================================================
def get_items_by_room(room_id):
    return get_db().execute("""
        SELECT id, item_name, quantity, status, remarks
        FROM room_items
        WHERE room_id = ?
        ORDER BY item_name
    """, (room_id,)).fetchall()


# =====================================================
# DELETE ITEM (CONTROLLED)
# =====================================================
def delete_item(item_id):
    db = get_db()
    db.execute("DELETE FROM room_items WHERE id = ?", (item_id,))
    db.commit()
