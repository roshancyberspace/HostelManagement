from datetime import date, timedelta

from models.db import get_db
from models.floor_model import _uses_block_schema, floor_label_sql, floor_order_sql

OVERDUE_DAYS = 7


def _hostel_filters(alias="h", hostel_id=None):
    if hostel_id:
        return f"WHERE {alias}.id = ?", [hostel_id]
    return "", []


def get_room_report(room_id):
    db = get_db()

    room = db.execute(
        f"""
        SELECT
            r.id,
            r.room_no,
            r.status,
            r.ac_type,
            {floor_label_sql("f")} AS floor_no
        FROM rooms r
        JOIN floors f ON r.floor_id = f.id
        WHERE r.id = ?
        """,
        (room_id,),
    ).fetchone()

    inspections = db.execute(
        """
        SELECT
            inspection_type,
            remarks,
            damage,
            fine,
            inspected_on
        FROM inspections
        WHERE target_type = 'ROOM'
          AND target_id = ?
        ORDER BY inspected_on DESC
        """,
        (room_id,),
    ).fetchall()

    recoveries = db.execute(
        """
        SELECT
            amount,
            reason,
            created_on
        FROM recovery_ledger
        WHERE target_type = 'ROOM'
          AND target_id = ?
        ORDER BY created_on DESC
        """,
        (room_id,),
    ).fetchall()

    items = db.execute(
        """
        SELECT
            item_name,
            quantity,
            status,
            remarks
        FROM room_items
        WHERE room_id = ?
        ORDER BY item_name
        """,
        (room_id,),
    ).fetchall()

    return {"room": room, "inspections": inspections, "recoveries": recoveries, "items": items}


def get_floor_report(floor_id):
    db = get_db()
    limit_date = date.today() - timedelta(days=OVERDUE_DAYS)

    rooms = db.execute(
        """
        SELECT
            r.id,
            r.room_no,
            r.status,
            (
                SELECT MAX(inspected_on)
                FROM inspections
                WHERE target_type = 'ROOM'
                  AND target_id = r.id
            ) AS last_inspection
        FROM rooms r
        WHERE r.floor_id = ?
        ORDER BY r.room_no
        """,
        (floor_id,),
    ).fetchall()

    summary = {"GOOD": 0, "DAMAGED": 0, "OVERDUE": 0}
    processed = []

    for room in rooms:
        if not room["last_inspection"] or room["last_inspection"] < str(limit_date):
            heat = "overdue"
            summary["OVERDUE"] += 1
        elif room["status"] == "DAMAGED":
            heat = "damaged"
            summary["DAMAGED"] += 1
        else:
            heat = "good"
            summary["GOOD"] += 1

        processed.append({"room_no": room["room_no"], "heat": heat, "last_inspection": room["last_inspection"]})

    return {"rooms": processed, "summary": summary}


def get_hostel_report():
    db = get_db()

    total_rooms = db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
    damaged_rooms = db.execute("SELECT COUNT(*) FROM rooms WHERE status = 'DAMAGED'").fetchone()[0]
    recovery_total = db.execute("SELECT COALESCE(SUM(amount), 0) FROM recovery_ledger").fetchone()[0]
    inspection_count = db.execute("SELECT COUNT(*) FROM inspections").fetchone()[0]
    total_floors = db.execute("SELECT COUNT(*) FROM floors").fetchone()[0]
    total_common = db.execute("SELECT COUNT(*) FROM common_areas").fetchone()[0]

    if _uses_block_schema():
        hostel_breakdown = db.execute(
            """
            SELECT
                h.id,
                h.name,
                COUNT(DISTINCT f.id) AS total_floors,
                COUNT(DISTINCT r.id) AS total_rooms,
                COUNT(DISTINCT CASE WHEN r.status = 'DAMAGED' THEN r.id END) AS damaged_rooms,
                COUNT(DISTINCT i.id) AS inspections,
                COALESCE(SUM(DISTINCT rec.amount), 0) AS recovery_total
            FROM hostels h
            LEFT JOIN blocks b ON b.hostel_id = h.id
            LEFT JOIN floors f ON f.block_id = b.id
            LEFT JOIN rooms r ON r.floor_id = f.id
            LEFT JOIN inspections i ON i.target_type = 'ROOM' AND i.target_id = r.id
            LEFT JOIN recovery_ledger rec ON rec.target_type = 'ROOM' AND rec.target_id = r.id
            GROUP BY h.id, h.name
            ORDER BY h.name
            """
        ).fetchall()
    else:
        hostel_breakdown = db.execute(
            """
            SELECT
                h.id,
                h.name,
                COUNT(DISTINCT f.id) AS total_floors,
                COUNT(DISTINCT r.id) AS total_rooms,
                COUNT(DISTINCT CASE WHEN r.status = 'DAMAGED' THEN r.id END) AS damaged_rooms,
                COUNT(DISTINCT i.id) AS inspections,
                COALESCE(SUM(DISTINCT rec.amount), 0) AS recovery_total
            FROM hostels h
            LEFT JOIN floors f ON f.school_id = h.id
            LEFT JOIN rooms r ON r.floor_id = f.id
            LEFT JOIN inspections i ON i.target_type = 'ROOM' AND i.target_id = r.id
            LEFT JOIN recovery_ledger rec ON rec.target_type = 'ROOM' AND rec.target_id = r.id
            GROUP BY h.id, h.name
            ORDER BY h.name
            """
        ).fetchall()

    return {
        "total_rooms": total_rooms,
        "damaged_rooms": damaged_rooms,
        "recovery_total": recovery_total,
        "inspection_count": inspection_count,
        "total_floors": total_floors,
        "total_common": total_common,
        "hostel_breakdown": hostel_breakdown,
    }


def get_floor_heatmap(hostel_id=None):
    db = get_db()
    params = []

    if _uses_block_schema():
        where_sql, params = _hostel_filters("h", hostel_id)
        rows = db.execute(
            f"""
            SELECT
                h.id AS hostel_id,
                h.name AS hostel,
                COALESCE(b.name, 'General') AS block,
                {floor_label_sql("f")} AS floor,
                COUNT(DISTINCT r.id) AS total_rooms,
                COUNT(DISTINCT CASE WHEN r.status = 'DAMAGED' THEN r.id END) AS damaged_rooms,
                COUNT(DISTINCT CASE WHEN i.target_id IS NOT NULL THEN r.id END) AS inspected_rooms
            FROM floors f
            LEFT JOIN blocks b ON b.id = f.block_id
            LEFT JOIN hostels h ON h.id = b.hostel_id
            LEFT JOIN rooms r ON r.floor_id = f.id
            LEFT JOIN (
                SELECT DISTINCT target_id
                FROM inspections
                WHERE target_type = 'ROOM'
            ) i ON i.target_id = r.id
            {where_sql}
            GROUP BY f.id, h.id, h.name, block, floor
            ORDER BY h.name, block, {floor_order_sql("f")}
            """,
            params,
        ).fetchall()
    else:
        where_sql, params = _hostel_filters("h", hostel_id)
        rows = db.execute(
            f"""
            SELECT
                h.id AS hostel_id,
                h.name AS hostel,
                COALESCE(b.name, 'General') AS block,
                {floor_label_sql("f")} AS floor,
                COUNT(DISTINCT r.id) AS total_rooms,
                COUNT(DISTINCT CASE WHEN r.status = 'DAMAGED' THEN r.id END) AS damaged_rooms,
                COUNT(DISTINCT CASE WHEN i.target_id IS NOT NULL THEN r.id END) AS inspected_rooms
            FROM floors f
            LEFT JOIN hostels h ON h.id = f.school_id
            LEFT JOIN blocks b ON b.hostel_id = h.id
            LEFT JOIN rooms r ON r.floor_id = f.id
            LEFT JOIN (
                SELECT DISTINCT target_id
                FROM inspections
                WHERE target_type = 'ROOM'
            ) i ON i.target_id = r.id
            {where_sql}
            GROUP BY f.id, h.id, h.name, block, floor
            ORDER BY h.name, block, {floor_order_sql("f")}
            """,
            params,
        ).fetchall()

    heatmap = []
    for row in rows:
        total = row["total_rooms"] or 0
        inspected = row["inspected_rooms"] or 0
        damaged = row["damaged_rooms"] or 0
        percent = int((inspected / total) * 100) if total else 0
        health = "safe"
        if damaged > 0:
            health = "danger"
        elif percent < 100:
            health = "warning"

        heatmap.append(
            {
                "hostel_id": row["hostel_id"],
                "hostel": row["hostel"],
                "block": row["block"],
                "floor": row["floor"],
                "total": total,
                "damaged": damaged,
                "inspected": inspected,
                "percent": percent,
                "health": health,
            }
        )

    return heatmap
