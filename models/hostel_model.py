from models.db import get_db

# =====================================================
# CREATE HOSTEL
# =====================================================
def add_hostel(name):
    db = get_db()
    db.execute(
        "INSERT INTO hostels (name) VALUES (?)",
        (name,)
    )
    db.commit()


# =====================================================
# GET ALL HOSTELS
# =====================================================
def get_hostels():
    return get_db().execute(
        "SELECT * FROM hostels ORDER BY name"
    ).fetchall()


# =====================================================
# SAFE DELETE CHECK
# =====================================================
def can_delete_hostel(hostel_id):
    db = get_db()

    blocks = db.execute(
        "SELECT COUNT(*) FROM blocks WHERE hostel_id=?",
        (hostel_id,)
    ).fetchone()[0]

    return blocks == 0


# =====================================================
# DELETE HOSTEL (SAFE)
# =====================================================
def delete_hostel(hostel_id):
    if not can_delete_hostel(hostel_id):
        raise Exception(
            "❌ Cannot delete hostel. Remove all blocks under this hostel first."
        )

    db = get_db()
    db.execute(
        "DELETE FROM hostels WHERE id=?",
        (hostel_id,)
    )
    db.commit()
