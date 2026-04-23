from models.db import get_db
from models.floor_model import (
    floor_label_sql,
    floor_order_sql,
    block_join_sql,
    hostel_join_sql,
)

# =====================================================
# CREATE COMMON AREA (FLOOR-WISE)
# =====================================================
def add_common_area(floor_id, name):
    db = get_db()
    db.execute(
        """
        INSERT INTO common_areas (floor_id, area_name, status)
        VALUES (?, ?, 'GOOD')
        """,
        (floor_id, name)
    )
    db.commit()


# =====================================================
# GET ALL COMMON AREAS (USED BY STRUCTURE & INSPECTION)
# =====================================================
def get_common_areas():
    return get_db().execute(
        f"""
        SELECT
            c.id,
            c.area_name,
            c.status,
            {floor_label_sql("f")} AS floor_no,
            COALESCE(b.name, 'General') AS block_name,
            h.name AS hostel_name
        FROM common_areas c
        JOIN floors f ON f.id = c.floor_id
        {block_join_sql("f")}
        {hostel_join_sql("f")}
        ORDER BY h.name, block_name, {floor_order_sql("f")}, c.area_name
        """
    ).fetchall()


# =====================================================
# GET COMMON AREAS BY FLOOR (API USE)
# =====================================================
def get_common_areas_by_floor(floor_id):
    return get_db().execute(
        """
        SELECT id, area_name, status
        FROM common_areas
        WHERE floor_id = ?
        ORDER BY area_name
        """
    ).fetchall()


# =====================================================
# UPDATE STATUS (INSPECTION / MAINTENANCE)
# =====================================================
def update_status(area_id, status):
    db = get_db()
    db.execute(
        """
        UPDATE common_areas
        SET status = ?
        WHERE id = ?
        """,
        (status, area_id)
    )
    db.commit()


# =====================================================
# DELETE COMMON AREA (CONTROLLED)
# =====================================================
def delete_common_area(area_id):
    db = get_db()
    db.execute(
        "DELETE FROM common_areas WHERE id = ?",
        (area_id,)
    )
    db.commit()
