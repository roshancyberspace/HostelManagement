from models.db import get_db
from models.floor_model import floor_label_sql


def add_recovery(target_type, target_id, amount, reason):
    db = get_db()
    db.execute(
        """
        INSERT INTO recovery_ledger
        (target_type, target_id, amount, reason, created_on)
        VALUES (?, ?, ?, ?, DATE('now'))
        """,
        (target_type, target_id, amount, reason),
    )
    db.commit()


def get_recoveries(target_type=None, search=""):
    db = get_db()
    where = []
    params = []

    if target_type:
        where.append("r.target_type = ?")
        params.append(target_type)

    if search:
        token = f"%{search}%"
        where.append(
            """
            (
                CAST(r.target_id AS TEXT) LIKE ?
                OR COALESCE(room.room_no, '') LIKE ?
                OR COALESCE(ca.area_name, '') LIKE ?
                OR COALESCE(h_room.name, h_common.name, '') LIKE ?
                OR COALESCE(b_room.name, b_common.name, '') LIKE ?
                OR COALESCE(room_floor.floor_no, common_floor.floor_no, '') LIKE ?
                OR COALESCE(r.reason, '') LIKE ?
            )
            """
        )
        params.extend([token, token, token, token, token, token, token])

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    return db.execute(
        f"""
        SELECT DISTINCT
            r.id,
            r.target_type,
            r.target_id,
            r.amount,
            r.reason,
            r.created_on,
            COALESCE(room.room_no, ca.area_name, 'Target ' || r.target_id) AS target_name,
            COALESCE(h_room.name, h_common.name, '-') AS hostel_name,
            '-' AS block_name,
            COALESCE(room_floor.floor_no, common_floor.floor_no, '-') AS floor_name
        FROM recovery_ledger r
        LEFT JOIN rooms room
            ON r.target_type = 'ROOM' AND room.id = r.target_id
        LEFT JOIN floors rf ON rf.id = room.floor_id
        LEFT JOIN common_areas ca
            ON r.target_type = 'COMMON' AND ca.id = r.target_id
        LEFT JOIN floors cf ON cf.id = ca.floor_id
        LEFT JOIN hostels h_room ON h_room.id = rf.school_id
        LEFT JOIN hostels h_common ON h_common.id = cf.school_id
        LEFT JOIN (
            SELECT
                f.id,
                {floor_label_sql('f')} AS floor_no
            FROM floors f
        ) room_floor ON room_floor.id = rf.id
        LEFT JOIN (
            SELECT
                f.id,
                {floor_label_sql('f')} AS floor_no
            FROM floors f
        ) common_floor ON common_floor.id = cf.id
        {where_sql}
        ORDER BY r.created_on DESC, r.id DESC
        """,
        params,
    ).fetchall()
