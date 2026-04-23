from models.db import get_db
from models.floor_model import floor_label_sql, floor_order_sql, block_join_sql, hostel_join_sql

# =====================================================
# CREATE ROOM (WITH AC / NON-AC SUPPORT)
# =====================================================
def add_room(floor_id, room_no, ac_type="NON_AC"):
    db = get_db()
    db.execute(
        """
        INSERT INTO rooms (floor_id, room_no, status, ac_type)
        VALUES (?, ?, 'GOOD', ?)
        """,
        (floor_id, room_no, ac_type)
    )
    db.commit()


# =====================================================
# GET ALL ROOMS (STRUCTURE / REPORTS / DASHBOARD)
# =====================================================
def get_rooms():
    return get_db().execute(f"""
        SELECT
            r.id,
            r.room_no,
            r.status,
            r.ac_type,
            r.floor_id,
            COUNT(DISTINCT bed.id) AS total_beds,
            COUNT(DISTINCT CASE WHEN UPPER(bed.status) = 'OCCUPIED' THEN bed.id END) AS occupied_beds,
            COUNT(DISTINCT CASE WHEN a.status = 'ALLOTTED' THEN a.ledger_number END) AS allotted_students,
            {floor_label_sql("f")} AS floor_no,
            COALESCE(b.name, 'General') AS block_name,
            h.name AS hostel_name
        FROM rooms r
        JOIN floors f ON f.id = r.floor_id
        {block_join_sql("f")}
        {hostel_join_sql("f")}
        LEFT JOIN beds bed ON bed.room_id = r.id
        LEFT JOIN bed_allotments a ON a.bed_id = bed.id AND a.status = 'ALLOTTED'
        GROUP BY r.id, r.room_no, r.status, r.ac_type, r.floor_id, floor_no, block_name, h.name
        ORDER BY h.name, block_name, {floor_order_sql("f")}, r.room_no
    """).fetchall()


# =====================================================
# GET ROOMS BY FLOOR (DROPDOWNS)
# =====================================================
def get_rooms_by_floor(floor_id):
    return get_db().execute(
        """
        SELECT id, room_no
        FROM rooms
        WHERE floor_id=?
        ORDER BY room_no
        """,
        (floor_id,)
    ).fetchall()


# =====================================================
# UPDATE ROOM STATUS (AUTO FROM INSPECTION)
# =====================================================
def update_status(room_id, status):
    db = get_db()
    db.execute(
        "UPDATE rooms SET status=? WHERE id=?",
        (status, room_id)
    )
    db.commit()


# =====================================================
# UPDATE AC TYPE (MANUAL)
# =====================================================
def update_ac_type(room_id, ac_type):
    db = get_db()
    db.execute(
        "UPDATE rooms SET ac_type=? WHERE id=?",
        (ac_type, room_id)
    )
    db.commit()


# =====================================================
# TOGGLE AC ↔ NON-AC (INLINE BUTTON)
# =====================================================
def toggle_ac(room_id):
    db = get_db()
    db.execute(
        """
        UPDATE rooms
        SET ac_type =
            CASE
                WHEN ac_type='AC' THEN 'NON_AC'
                ELSE 'AC'
            END
        WHERE id=?
        """,
        (room_id,)
    )
    db.commit()


# =====================================================
# SAFE DELETE CHECK
# =====================================================
def can_delete_room(room_id):
    db = get_db()

    beds = db.execute(
        "SELECT COUNT(*) FROM beds WHERE room_id=?",
        (room_id,)
    ).fetchone()[0]

    items = db.execute(
        "SELECT COUNT(*) FROM room_items WHERE room_id=?",
        (room_id,)
    ).fetchone()[0]

    inspections = db.execute(
        """
        SELECT COUNT(*)
        FROM inspections
        WHERE target_type='ROOM' AND target_id=?
        """,
        (room_id,)
    ).fetchone()[0]

    return beds == 0 and items == 0 and inspections == 0


# =====================================================
# DELETE ROOM (SAFE & CONTROLLED)
# =====================================================
def delete_room(room_id):
    if not can_delete_room(room_id):
        raise Exception(
            "❌ Cannot delete room. Remove beds, items, and inspection records first."
        )

    db = get_db()
    db.execute("DELETE FROM rooms WHERE id=?", (room_id,))
    db.commit()
