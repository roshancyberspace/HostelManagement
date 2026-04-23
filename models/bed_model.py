from models.db import get_db
from models.floor_model import floor_label_sql, floor_order_sql, _uses_block_schema


def add_bed(room_id, bed_no):
    db = get_db()
    db.execute(
        """
        INSERT INTO beds (room_id, bed_no, status)
        VALUES (?, ?, 'AVAILABLE')
        """,
        (room_id, bed_no)
    )
    db.commit()


def get_all_beds():
    if _uses_block_schema():
        block_join = "JOIN blocks b2 ON b2.id = f.block_id"
        hostel_join = "JOIN hostels h ON h.id = b2.hostel_id"
    else:
        block_join = "LEFT JOIN blocks b2 ON b2.hostel_id = f.school_id"
        hostel_join = "JOIN hostels h ON h.id = f.school_id"

    return get_db().execute(f"""
        SELECT
            b.id,
            b.bed_no,
            b.status,
            b.room_id,
            r.room_no,
            {floor_label_sql("f")} AS floor_no,
            COALESCE(b2.name, 'General') AS block_name,
            h.name AS hostel_name
        FROM beds b
        JOIN rooms r ON r.id = b.room_id
        JOIN floors f ON f.id = r.floor_id
        {block_join}
        {hostel_join}
        ORDER BY h.name, block_name, {floor_order_sql("f")}, r.room_no, b.bed_no
    """).fetchall()


def update_status(bed_id, status):
    db = get_db()
    db.execute(
        "UPDATE beds SET status=? WHERE id=?",
        (status, bed_id)
    )
    db.commit()


def can_delete_bed(bed_id):
    db = get_db()

    allocations = db.execute(
        """
        SELECT COUNT(*)
        FROM bed_allocations
        WHERE bed_id=?
        """,
        (bed_id,)
    ).fetchone()[0] if table_exists("bed_allocations") else 0

    return allocations == 0


def table_exists(name):
    db = get_db()
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,)
    ).fetchone()
    return row is not None


def delete_bed(bed_id):
    if not can_delete_bed(bed_id):
        raise Exception(
            "Cannot delete bed. It is allocated or has history."
        )

    db = get_db()
    db.execute(
        "DELETE FROM beds WHERE id=?",
        (bed_id,)
    )
    db.commit()
