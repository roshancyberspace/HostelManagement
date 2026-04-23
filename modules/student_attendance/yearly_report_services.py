from models.db import get_db


def yearly_attendance_summary(year):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            substr(attendance_date, 1, 7) AS month,
            COUNT(*) AS total,
            SUM(CASE WHEN status='PRESENT' THEN 1 ELSE 0 END) AS present
        FROM student_attendance
        WHERE substr(attendance_date, 1, 4) = ?
        GROUP BY month
        ORDER BY month
    """, (str(year),))

    rows = cur.fetchall()
    conn.close()
    return rows
