from models.db import get_db
from models.floor_model import _uses_block_schema


def add_block(hostel_id, name):
    db = get_db()
    db.execute(
        "INSERT INTO blocks (hostel_id, name) VALUES (?, ?)",
        (hostel_id, name)
    )
    db.commit()


def get_blocks():
    return get_db().execute("""
        SELECT
            b.id,
            b.name,
            b.hostel_id,
            h.name AS hostel_name
        FROM blocks b
        JOIN hostels h ON h.id = b.hostel_id
        ORDER BY h.name, b.name
    """).fetchall()


def can_delete_block(block_id):
    db = get_db()

    if _uses_block_schema():
        floors = db.execute(
            "SELECT COUNT(*) FROM floors WHERE block_id=?",
            (block_id,)
        ).fetchone()[0]
    else:
        hostel = db.execute(
            "SELECT hostel_id FROM blocks WHERE id=?",
            (block_id,)
        ).fetchone()
        if not hostel:
            return True

        floors = db.execute(
            "SELECT COUNT(*) FROM floors WHERE school_id=?",
            (hostel["hostel_id"],)
        ).fetchone()[0]

    return floors == 0


def delete_block(block_id):
    if not can_delete_block(block_id):
        raise Exception(
            "Cannot delete block. Remove all floors under this block first."
        )

    db = get_db()
    db.execute(
        "DELETE FROM blocks WHERE id=?",
        (block_id,)
    )
    db.commit()
