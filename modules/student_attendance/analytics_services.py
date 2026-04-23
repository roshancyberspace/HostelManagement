from models.db import get_db
from datetime import date, timedelta


# ==================================================
# ATTENDANCE PERCENTAGE BY CLASS
# ==================================================

def attendance_percentage_by_class(start_date, end_date):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            json_extract(snapshot, '$.class') AS class,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'PRESENT' THEN 1 ELSE 0 END) AS present
        FROM student_attendance
        WHERE attendance_date BETWEEN ? AND ?
        GROUP BY class
        ORDER BY class
    """, (start_date, end_date))

    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        percent = round((r["present"] / r["total"]) * 100, 2) if r["total"] else 0
        result.append({
            "class": r["class"],
            "percentage": percent
        })
    return result


# ==================================================
# ATTENDANCE PERCENTAGE BY BLOCK
# ==================================================

def attendance_percentage_by_block(start_date, end_date):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            json_extract(snapshot, '$.block') AS block,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'PRESENT' THEN 1 ELSE 0 END) AS present
        FROM student_attendance
        WHERE attendance_date BETWEEN ? AND ?
        GROUP BY block
        ORDER BY block
    """, (start_date, end_date))

    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        percent = round((r["present"] / r["total"]) * 100, 2) if r["total"] else 0
        result.append({
            "block": r["block"],
            "percentage": percent
        })
    return result


# ==================================================
# GATEPASS TREND
# ==================================================

def gatepass_trend(start_date, end_date):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT attendance_date, COUNT(*) AS total
        FROM student_attendance
        WHERE is_gatepass = 1
          AND attendance_date BETWEEN ? AND ?
        GROUP BY attendance_date
        ORDER BY attendance_date
    """, (start_date, end_date))

    rows = cur.fetchall()
    conn.close()
    return rows


# ==================================================
# CHRONIC ABSENTEES
# ==================================================

def chronic_absentees(start_date, end_date, limit=10):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sa.ledger_no,
            COALESCE(s.student_name, 'Student') AS student_name,
            COALESCE(s.class, 'Unassigned') AS class,
            COUNT(*) AS absents
        FROM student_attendance sa
        LEFT JOIN students s ON sa.ledger_no = s.ledger_no
        WHERE sa.status = 'ABSENT'
          AND sa.attendance_date BETWEEN ? AND ?
        GROUP BY sa.ledger_no, s.student_name, s.class
        ORDER BY absents DESC, student_name
        LIMIT ?
    """, (start_date, end_date, limit))

    rows = cur.fetchall()
    conn.close()
    return rows
