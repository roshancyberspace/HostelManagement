from models.db import get_db
from datetime import date, timedelta
import calendar


def get_previous_month_range():
    today = date.today()
    first_this_month = today.replace(day=1)
    last_prev_month = first_this_month - timedelta(days=1)
    first_prev_month = last_prev_month.replace(day=1)
    return first_prev_month, last_prev_month


# ==================================================
# MONTHLY SUMMARY (CLASS + BLOCK)
# ==================================================

def monthly_attendance_summary(start_date, end_date):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            json_extract(snapshot, '$.class') AS class,
            json_extract(snapshot, '$.block') AS block,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'PRESENT' THEN 1 ELSE 0 END) AS present,
            SUM(CASE WHEN is_gatepass = 1 THEN 1 ELSE 0 END) AS gatepass
        FROM student_attendance
        WHERE attendance_date BETWEEN ? AND ?
        GROUP BY class, block
        ORDER BY class, block
    """, (start_date, end_date))

    rows = cur.fetchall()
    conn.close()
    return rows


# ==================================================
# CHRONIC ABSENTEES (MONTHLY)
# ==================================================

def monthly_chronic_absentees(start_date, end_date, threshold=5):
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
        HAVING absents >= ?
        ORDER BY absents DESC, student_name
    """, (start_date, end_date, threshold))

    rows = cur.fetchall()
    conn.close()
    return rows
