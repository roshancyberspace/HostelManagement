from models.db import get_db
from datetime import date, timedelta


def get_overdue_common_areas(days=30):
    db = get_db()
    cutoff = date.today() - timedelta(days=days)

    return db.execute("""
        SELECT
            c.area_name,
            f.floor_name,
            MAX(i.inspected_on) AS last_inspected
        FROM common_areas c
        JOIN floors f ON f.id = c.floor_id
        LEFT JOIN inspections i
            ON i.target_type='COMMON' AND i.target_id=c.id
        GROUP BY c.id, c.area_name, f.floor_name
        HAVING last_inspected IS NULL OR last_inspected < ?
        ORDER BY f.floor_name, c.area_name
    """, (cutoff,)).fetchall()
