from models.db import get_db
from datetime import date

# -------------------------
# STOCK MASTER
# -------------------------
def add_stock_item(name, category, unit):
    db = get_db()
    db.execute(
        "INSERT INTO stock_items (item_name, category, unit) VALUES (?, ?, ?)",
        (name, category, unit)
    )
    db.commit()

def get_stock_items():
    return get_db().execute(
        "SELECT * FROM stock_items WHERE active=1 ORDER BY item_name"
    ).fetchall()

# -------------------------
# ASSIGN STOCK
# -------------------------
def assign_stock(target_type, target_id, item_id, qty):
    db = get_db()
    cur = db.execute("""
        INSERT INTO stock_allocations
        (target_type, target_id, item_id, quantity)
        VALUES (?, ?, ?, ?)
    """, (target_type, target_id, item_id, qty))
    allocation_id = cur.lastrowid

    db.execute("""
        INSERT INTO stock_history
        (allocation_id, action, remarks, action_date)
        VALUES (?, 'ASSIGNED', '', ?)
    """, (allocation_id, date.today()))
    db.commit()

# -------------------------
# GET STOCK BY LOCATION
# -------------------------
def get_room_stock(room_id):
    return get_db().execute("""
        SELECT sa.id, si.item_name, sa.quantity, sa.status
        FROM stock_allocations sa
        JOIN stock_items si ON sa.item_id = si.id
        WHERE sa.target_type='ROOM' AND sa.target_id=?
    """, (room_id,)).fetchall()

def get_area_stock(area_id):
    return get_db().execute("""
        SELECT sa.id, si.item_name, sa.quantity, sa.status
        FROM stock_allocations sa
        JOIN stock_items si ON sa.item_id = si.id
        WHERE sa.target_type='COMMON' AND sa.target_id=?
    """, (area_id,)).fetchall()

# -------------------------
# STATUS UPDATES
# -------------------------
def update_stock_status(allocation_id, status, remarks=""):
    db = get_db()
    db.execute(
        "UPDATE stock_allocations SET status=? WHERE id=?",
        (status, allocation_id)
    )
    db.execute("""
        INSERT INTO stock_history
        (allocation_id, action, remarks, action_date)
        VALUES (?, ?, ?, ?)
    """, (allocation_id, status, remarks, date.today()))
    db.commit()
