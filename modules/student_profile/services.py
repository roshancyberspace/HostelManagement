from datetime import datetime

from models.db import get_db
from modules.student_master.services import get_student_full_by_ledger


def _flatten_student_record(data):
    if not data:
        return None

    student = data["student"]
    biodata = data.get("biodata")
    parents = data.get("parents")
    guardians = data.get("guardians") or []

    guardian_contact = None
    if parents:
        guardian_contact = parents["father_mobile_1"] or parents["mother_mobile_1"]
    if not guardian_contact and guardians:
        guardian_contact = guardians[0]["mobile_1"]

    return {
        "student_id": student["id"],
        "ledger_no": student["ledger_no"],
        "full_name": student["student_name"],
        "class": student["class"],
        "section": student["section"],
        "status": student["status"],
        "biodata_completed": student["biodata_completed"],
        "remarks": biodata["remarks"] if biodata else "",
        "dob": biodata["dob"] if biodata else "",
        "class_of_admission": biodata["class_of_admission"] if biodata else "",
        "date_of_admission": biodata["date_of_admission"] if biodata else "",
        "hostel_reporting_date": biodata["hostel_reporting_date"] if biodata else "",
        "joining_date": (
            (biodata["hostel_reporting_date"] if biodata else None)
            or (biodata["date_of_admission"] if biodata else None)
            or ""
        ),
        "permanent_address": biodata["permanent_address"] if biodata else "",
        "father_name": parents["father_name"] if parents else "",
        "mother_name": parents["mother_name"] if parents else "",
        "guardian_contact": guardian_contact or "",
        "guardians": guardians,
    }


def create_student(data):
    db = get_db()
    session_row = db.execute("""
        SELECT id FROM academic_sessions
        WHERE is_active = 1 AND is_deleted = 0
        LIMIT 1
    """).fetchone()

    if not session_row:
        raise Exception("No active academic session found")

    db.execute("""
        INSERT INTO students
        (ledger_no, student_name, class, section, session_id, status, biodata_completed)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', 0)
    """, (
        data["ledger_no"],
        data["full_name"],
        data["class"],
        data.get("section"),
        session_row["id"],
    ))
    db.commit()


def get_all_students(search=None, status="ALL"):
    db = get_db()
    query = """
        SELECT
            s.id,
            s.ledger_no,
            s.student_name AS full_name,
            s.class,
            s.section,
            s.status,
            s.biodata_completed,
            b.remarks,
            b.hostel_reporting_date,
            b.date_of_admission,
            p.father_name,
            p.mother_name,
            COALESCE(p.father_mobile_1, p.mother_mobile_1) AS guardian_contact
        FROM students s
        LEFT JOIN student_biodata b ON b.student_id = s.id
        LEFT JOIN student_parents p ON p.student_id = s.id
    """

    conditions = []
    params = []

    if status and status != "ALL":
        conditions.append("s.status = ?")
        params.append(status)

    if search:
        like_search = f"%{search.strip()}%"
        conditions.append("""
            (
                s.ledger_no LIKE ?
                OR s.student_name LIKE ?
                OR s.class LIKE ?
                OR s.section LIKE ?
                OR COALESCE(p.father_name, '') LIKE ?
                OR COALESCE(p.mother_name, '') LIKE ?
            )
        """)
        params.extend([like_search] * 6)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY s.student_name COLLATE NOCASE, s.ledger_no"
    return db.execute(query, tuple(params)).fetchall()


def get_student(ledger_no):
    return _flatten_student_record(get_student_full_by_ledger(ledger_no))


def update_student(ledger_no, data):
    db = get_db()
    student = db.execute(
        "SELECT id FROM students WHERE ledger_no = ?",
        (ledger_no,),
    ).fetchone()
    if not student:
        raise Exception("Student not found")

    student_id = student["id"]

    db.execute("""
        UPDATE students
        SET student_name = ?, class = ?, section = ?, status = ?
        WHERE ledger_no = ?
    """, (
        data["full_name"],
        data["class"],
        data["section"],
        data.get("status", "ACTIVE"),
        ledger_no,
    ))

    biodata_exists = db.execute(
        "SELECT id FROM student_biodata WHERE student_id = ?",
        (student_id,),
    ).fetchone()
    if biodata_exists:
        db.execute("""
            UPDATE student_biodata
            SET remarks = ?, permanent_address = ?, date_of_admission = ?,
                hostel_reporting_date = ?, dob = ?
            WHERE student_id = ?
        """, (
            data.get("remarks"),
            data.get("permanent_address"),
            data.get("date_of_admission"),
            data.get("hostel_reporting_date"),
            data.get("dob"),
            student_id,
        ))
    else:
        db.execute("""
            INSERT INTO student_biodata
            (student_id, remarks, permanent_address, date_of_admission, hostel_reporting_date, dob)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            data.get("remarks"),
            data.get("permanent_address"),
            data.get("date_of_admission"),
            data.get("hostel_reporting_date"),
            data.get("dob"),
        ))

    parents_exists = db.execute(
        "SELECT 1 FROM student_parents WHERE student_id = ?",
        (student_id,),
    ).fetchone()
    if parents_exists:
        db.execute("""
            UPDATE student_parents
            SET father_name = ?, mother_name = ?, father_mobile_1 = ?
            WHERE student_id = ?
        """, (
            data.get("father_name"),
            data.get("mother_name"),
            data.get("guardian_contact"),
            student_id,
        ))
    else:
        db.execute("""
            INSERT INTO student_parents
            (student_id, father_name, mother_name, father_mobile_1)
            VALUES (?, ?, ?, ?)
        """, (
            student_id,
            data.get("father_name"),
            data.get("mother_name"),
            data.get("guardian_contact"),
        ))

    db.commit()


def add_behaviour_log(ledger_no, behaviour_type, severity, title, description, recorded_by):
    db = get_db()
    cur = db.cursor()
    cur.execute("PRAGMA table_info(student_behaviour_log)")
    columns = {row["name"] for row in cur.fetchall()}

    if "severity" in columns:
        db.execute("""
            INSERT INTO student_behaviour_log
            (ledger_no, behaviour_type, severity, title, description, recorded_by, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ledger_no, behaviour_type, severity,
            title, description, recorded_by,
            datetime.now().isoformat()
        ))
    else:
        db.execute("""
            INSERT INTO student_behaviour_log
            (ledger_no, behaviour_type, title, description, recorded_by, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ledger_no, behaviour_type,
            title, description, recorded_by,
            datetime.now().isoformat()
        ))
    db.commit()


def get_behaviour_logs(ledger_no):
    db = get_db()
    return db.execute("""
        SELECT * FROM student_behaviour_log
        WHERE ledger_no = ?
        ORDER BY recorded_at DESC
    """, (ledger_no,)).fetchall()


def auto_behaviour_from_gatepass(ledger_no, status, approver):
    if status == "APPROVED":
        add_behaviour_log(
            ledger_no,
            "GOOD",
            "LOW",
            "Gate Pass Approved",
            "Student followed gate pass protocol",
            approver
        )
    elif status == "VIOLATION":
        add_behaviour_log(
            ledger_no,
            "BAD",
            "HIGH",
            "Gate Pass Violation",
            "Late return / misuse of permission",
            approver
        )


def get_student_summary(ledger_no):
    db = get_db()

    good = db.execute("""
        SELECT COUNT(*) c FROM student_behaviour_log
        WHERE ledger_no = ? AND behaviour_type='GOOD'
    """, (ledger_no,)).fetchone()["c"]

    bad = db.execute("""
        SELECT COUNT(*) c FROM student_behaviour_log
        WHERE ledger_no = ? AND behaviour_type='BAD'
    """, (ledger_no,)).fetchone()["c"]

    score = good - bad

    rating = (
        "EXCELLENT" if score >= 5 else
        "GOOD" if score >= 2 else
        "NEUTRAL" if score >= 0 else
        "NEEDS ATTENTION"
    )

    return {"good": good, "bad": bad, "score": score, "rating": rating}


def get_student_timeline(ledger_no):
    db = get_db()
    events = []

    student = get_student(ledger_no)
    if student and student["joining_date"]:
        events.append({
            "date": student["joining_date"],
            "title": "Joined Hostel",
            "type": "INFO"
        })

    logs = db.execute("""
        SELECT recorded_at AS date, title, behaviour_type AS type
        FROM student_behaviour_log
        WHERE ledger_no = ?
    """, (ledger_no,)).fetchall()

    for log in logs:
        events.append(dict(log))

    events.sort(key=lambda item: item["date"] or "")
    return events
