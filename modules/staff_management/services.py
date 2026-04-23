import sqlite3

from models.db import get_db
from .models import init_staff_tables


def generate_staff_code():
    """
    Generates STAFF0001, STAFF0002...
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM staff_master")
    count = cur.fetchone()[0]
    conn.close()
    return f"STAFF{count+1:04d}"


def get_all_staff(status=None, search=None, role=None, staff_code=None, department=None, phone=None):
    init_staff_tables()
    conn = get_db()
    cur = conn.cursor()

    conditions = []
    params = []

    if status and status != "ALL":
        conditions.append("status = ?")
        params.append(status)

    if search:
        conditions.append("(full_name LIKE ? OR designation LIKE ? OR staff_code LIKE ? OR department LIKE ? OR phone LIKE ?)")
        like_search = f"%{search.strip()}%"
        params.extend([like_search, like_search, like_search, like_search, like_search])

    if role:
        conditions.append("designation LIKE ?")
        params.append(f"%{role.strip()}%")

    if staff_code:
        conditions.append("(staff_code LIKE ? OR CAST(id AS TEXT) LIKE ?)")
        like_code = f"%{staff_code.strip()}%"
        params.extend([like_code, like_code])

    if department:
        conditions.append("department LIKE ?")
        params.append(f"%{department.strip()}%")

    if phone:
        conditions.append("(phone LIKE ? OR alternate_phone LIKE ?)")
        like_phone = f"%{phone.strip()}%"
        params.extend([like_phone, like_phone])

    query = "SELECT * FROM staff_master"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_staff_by_id(staff_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM staff_master WHERE id=?", (staff_id,))
    row = cur.fetchone()
    conn.close()
    return row


def create_staff(form):
    init_staff_tables()

    staff_code = generate_staff_code()
    full_name = (form.get("full_name") or "").strip()
    designation = (form.get("designation") or "").strip()

    if not full_name or not designation:
        return False, "Name and Designation are required."

    department = (form.get("department") or "HOSTEL").strip()
    phone = (form.get("phone") or "").strip()
    alternate_phone = (form.get("alternate_phone") or "").strip()
    email = (form.get("email") or "").strip()
    address = (form.get("address") or "").strip()
    joining_date = (form.get("joining_date") or "").strip()
    salary_monthly = form.get("salary_monthly") or 0
    remarks = (form.get("remarks") or "").strip()

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO staff_master
            (staff_code, full_name, designation, department, phone, alternate_phone, email,
             address, joining_date, salary_monthly, status, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
        """, (
            staff_code, full_name, designation, department, phone, alternate_phone, email,
            address, joining_date, float(salary_monthly), remarks
        ))
        conn.commit()
    except sqlite3.OperationalError as exc:
        conn.rollback()
        if "locked" in str(exc).lower():
            return False, "Database is busy right now. Please wait 5 to 10 seconds and try again."
        return False, f"Unable to save staff right now: {exc}"
    finally:
        conn.close()

    return True, f"Staff Created: {staff_code}"


def update_staff(staff_id, form):
    full_name = (form.get("full_name") or "").strip()
    designation = (form.get("designation") or "").strip()

    if not full_name or not designation:
        return False, "Name and Designation are required."

    department = (form.get("department") or "HOSTEL").strip()
    phone = (form.get("phone") or "").strip()
    alternate_phone = (form.get("alternate_phone") or "").strip()
    email = (form.get("email") or "").strip()
    address = (form.get("address") or "").strip()
    joining_date = (form.get("joining_date") or "").strip()
    salary_monthly = form.get("salary_monthly") or 0
    status = (form.get("status") or "ACTIVE").strip()
    remarks = (form.get("remarks") or "").strip()

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE staff_master
            SET full_name=?, designation=?, department=?, phone=?, alternate_phone=?, email=?,
                address=?, joining_date=?, salary_monthly=?, status=?, remarks=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            full_name, designation, department, phone, alternate_phone, email,
            address, joining_date, float(salary_monthly), status, remarks, staff_id
        ))
        conn.commit()
    except sqlite3.OperationalError as exc:
        conn.rollback()
        if "locked" in str(exc).lower():
            return False, "Database is busy right now. Please wait 5 to 10 seconds and try again."
        return False, f"Unable to update staff right now: {exc}"
    finally:
        conn.close()

    return True, "Staff Updated Successfully"
