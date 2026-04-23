from models.db import get_db


def _floor_columns():
    db = get_db()
    rows = db.execute("PRAGMA table_info(floors)").fetchall()
    return {row["name"] for row in rows}


def _uses_block_schema():
    cols = _floor_columns()
    return "block_id" in cols and "floor_no" in cols


def floor_label_sql(alias="f"):
    return f"{alias}.floor_no" if _uses_block_schema() else f"{alias}.floor_name"


def floor_order_sql(alias="f"):
    if _uses_block_schema():
        return f"{alias}.floor_no"

    return f"""
        CASE {alias}.floor_name
            WHEN 'Ground Floor' THEN 0
            WHEN 'First Floor' THEN 1
            WHEN 'Second Floor' THEN 2
            WHEN 'Third Floor' THEN 3
            WHEN 'Fourth Floor' THEN 4
            ELSE 99
        END,
        {alias}.floor_name
    """


def block_join_sql(alias="f"):
    if _uses_block_schema():
        return f"JOIN blocks b ON b.id = {alias}.block_id"
    return f"LEFT JOIN blocks b ON b.hostel_id = {alias}.school_id"


def hostel_join_sql(alias="f"):
    if _uses_block_schema():
        return f"JOIN hostels h ON h.id = b.hostel_id"
    return f"JOIN hostels h ON h.id = {alias}.school_id"


def add_floor(block_id, floor_no):
    db = get_db()
    if _uses_block_schema():
        db.execute(
            "INSERT INTO floors (block_id, floor_no) VALUES (?, ?)",
            (block_id, floor_no)
        )
    else:
        hostel_row = db.execute(
            "SELECT hostel_id FROM blocks WHERE id = ?",
            (block_id,)
        ).fetchone()
        if not hostel_row:
            raise Exception("Invalid block selected")

        db.execute(
            "INSERT INTO floors (school_id, floor_name) VALUES (?, ?)",
            (hostel_row["hostel_id"], str(floor_no).strip())
        )
    db.commit()


def get_floors():
    label_sql = floor_label_sql("f")
    order_sql = floor_order_sql("f")
    return get_db().execute(f"""
        SELECT
            f.id,
            {label_sql} AS floor_no,
            COALESCE(b.id, 0) AS block_id,
            COALESCE(b.name, 'General') AS block_name,
            h.name AS hostel_name
        FROM floors f
        {block_join_sql("f")}
        {hostel_join_sql("f")}
        ORDER BY h.name, block_name, {order_sql}
    """).fetchall()


def get_floors_for_block(block_id):
    db = get_db()
    label_sql = floor_label_sql("f")
    order_sql = floor_order_sql("f")

    if _uses_block_schema():
        return db.execute(f"""
            SELECT id, {label_sql} AS floor_no
            FROM floors f
            WHERE f.block_id = ?
            ORDER BY {order_sql}
        """, (block_id,)).fetchall()

    hostel_row = db.execute(
        "SELECT hostel_id FROM blocks WHERE id = ?",
        (block_id,)
    ).fetchone()
    if not hostel_row:
        return []

    return db.execute(f"""
        SELECT id, {label_sql} AS floor_no
        FROM floors f
        WHERE f.school_id = ?
        ORDER BY {order_sql}
    """, (hostel_row["hostel_id"],)).fetchall()


def can_delete_floor(floor_id):
    db = get_db()

    rooms = db.execute(
        "SELECT COUNT(*) FROM rooms WHERE floor_id=?",
        (floor_id,)
    ).fetchone()[0]

    common_areas = db.execute(
        "SELECT COUNT(*) FROM common_areas WHERE floor_id=?",
        (floor_id,)
    ).fetchone()[0]

    return rooms == 0 and common_areas == 0


def delete_floor(floor_id):
    if not can_delete_floor(floor_id):
        raise Exception(
            "Cannot delete floor. Remove all rooms and common areas first."
        )

    db = get_db()
    db.execute(
        "DELETE FROM floors WHERE id=?",
        (floor_id,)
    )
    db.commit()
