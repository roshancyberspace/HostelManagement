from datetime import date, datetime


# ==================================================
# HELPERS
# ==================================================
def today_str():
    """Store date as YYYY-MM-DD"""
    return date.today().isoformat()


def now_str():
    """Store datetime as YYYY-MM-DD HH:MM:SS"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==================================================
# SAFE STUDENT NAME COLUMN SUPPORT
# full_name OR student_name
# ==================================================
def get_active_student(db, ledger_no: str):
    """
    Returns student row safely (supports full_name OR student_name).
    Output has keys: ledger_no, full_name, status
    """
    cur = db.cursor()

    # ✅ Try full_name first
    try:
        cur.execute("""
            SELECT ledger_no, full_name AS full_name, status
            FROM students
            WHERE ledger_no = ?
            LIMIT 1
        """, (ledger_no.strip(),))
        return cur.fetchone()
    except Exception:
        # ✅ Fallback: student_name
        cur.execute("""
            SELECT ledger_no, student_name AS full_name, status
            FROM students
            WHERE ledger_no = ?
            LIMIT 1
        """, (ledger_no.strip(),))
        return cur.fetchone()


# ==================================================
# STUDENT ACTIVE BED CHECK
# ==================================================
def student_has_active_bed(db, ledger_no: str):
    """
    Returns active allotment row if any (status=ALLOTTED)
    """
    cur = db.cursor()
    cur.execute("""
        SELECT id, bed_id
        FROM bed_allotments
        WHERE ledger_number = ?
          AND status = 'ALLOTTED'
        ORDER BY id DESC
        LIMIT 1
    """, (ledger_no.strip(),))
    return cur.fetchone()


# ==================================================
# BED OCCUPIED CHECK (ALLOTMENTS TABLE)
# ==================================================
def bed_is_occupied(db, bed_id: int) -> bool:
    """
    Checks if bed_id has any active allotment
    """
    cur = db.cursor()
    cur.execute("""
        SELECT 1
        FROM bed_allotments
        WHERE bed_id = ?
          AND status = 'ALLOTTED'
        LIMIT 1
    """, (int(bed_id),))
    return cur.fetchone() is not None


# ==================================================
# FETCH VACANT BEDS LIST (DROPDOWN)
# ==================================================
def get_beds_for_allotment(db):
    """
    Returns only VACANT beds for AC student rooms.
    Fields returned:
      bed_id, floor_name, room_no, bed_no, status
    """
    cur = db.cursor()
    cur.execute("""
        SELECT
            b.id AS bed_id,
            f.floor_name AS floor_name,
            r.room_no AS room_no,
            b.bed_no AS bed_no,
            b.status AS status
        FROM beds b
        JOIN rooms r ON r.id = b.room_id
        JOIN floors f ON f.id = r.floor_id
        WHERE UPPER(b.status) = 'VACANT'
          AND UPPER(r.ac_type) = 'AC'
          AND r.bed_capacity > 0
        ORDER BY
          CASE f.floor_name
            WHEN 'Ground Floor' THEN 1
            WHEN 'First Floor' THEN 2
            WHEN 'Second Floor' THEN 3
            WHEN 'Third Floor' THEN 4
            ELSE 99
          END,
          CAST(r.room_no AS INTEGER),
          CAST(b.bed_no AS INTEGER)
    """)
    return cur.fetchall()


# ==================================================
# ALLOT BED (SAFE + UPDATES BED STATUS)
# ==================================================
def allot_bed(db, ledger_no: str, bed_id: int):
    """
    Allots a VACANT bed to ACTIVE student.
    Creates bed_allotments record and updates beds.status -> OCCUPIED.
    """
    ledger_no = ledger_no.strip()
    bed_id = int(bed_id)

    cur = db.cursor()

    # ---- Student validation ----
    cur.execute("""
        SELECT ledger_no, status
        FROM students
        WHERE ledger_no = ?
        LIMIT 1
    """, (ledger_no,))
    student = cur.fetchone()

    if not student:
        raise Exception("Invalid Ledger Number")

    # If status column exists, enforce ACTIVE only
    try:
        if str(student["status"]).upper() != "ACTIVE":
            raise Exception("Only ACTIVE hostel students can be allotted beds")
    except Exception:
        # If status missing/null, allow (but ideally status should exist)
        pass

    # ---- Prevent multiple active beds for same student ----
    if student_has_active_bed(db, ledger_no):
        raise Exception("Student already has an active bed")

    # ---- Bed validation ----
    cur.execute("""
        SELECT b.status, r.ac_type, r.bed_capacity
        FROM beds b
        JOIN rooms r ON r.id = b.room_id
        WHERE b.id = ?
        LIMIT 1
    """, (bed_id,))
    bed_row = cur.fetchone()

    if not bed_row:
        raise Exception("Invalid Bed Selected")

    if str(bed_row["status"]).upper() != "VACANT":
        raise Exception("Selected bed is not VACANT")

    # Only AC rooms allowed for student allotment
    if str(bed_row["ac_type"]).upper() != "AC":
        raise Exception("Only AC rooms are allowed for student allotment")

    if int(bed_row["bed_capacity"] or 0) <= 0:
        raise Exception("This room has 0 bed capacity")

    # Extra safety via allotments
    if bed_is_occupied(db, bed_id):
        raise Exception("Bed already occupied")

    # ---- Insert allotment ----
    cur.execute("""
        INSERT INTO bed_allotments
        (ledger_number, bed_id, allot_date, status, created_at)
        VALUES (?, ?, ?, 'ALLOTTED', ?)
    """, (ledger_no, bed_id, today_str(), now_str()))

    # ---- Update bed status ----
    cur.execute("""
        UPDATE beds
        SET status = 'OCCUPIED'
        WHERE id = ?
    """, (bed_id,))

    db.commit()


# ==================================================
# VACATE BED (MANUAL) + UPDATES BED STATUS
# ==================================================
def vacate_bed(db, ledger_no: str, reason: str = "VACATED"):
    """
    Vacates currently allotted bed for a ledger.
    Updates bed_allotments -> VACATED and beds.status -> VACANT
    """
    ledger_no = ledger_no.strip()
    reason = (reason or "VACATED").strip()

    cur = db.cursor()

    # Find active allotment
    cur.execute("""
        SELECT id, bed_id
        FROM bed_allotments
        WHERE ledger_number = ?
          AND status = 'ALLOTTED'
        ORDER BY id DESC
        LIMIT 1
    """, (ledger_no,))
    row = cur.fetchone()

    if not row:
        raise Exception("No ACTIVE bed allotment found for this student")

    allot_id = row["id"]
    bed_id = row["bed_id"]

    # Vacate allotment
    cur.execute("""
        UPDATE bed_allotments
        SET status = 'VACATED',
            vacate_date = ?,
            vacate_reason = ?
        WHERE id = ?
    """, (today_str(), reason, allot_id))

    # Mark bed VACANT again
    cur.execute("""
        UPDATE beds
        SET status = 'VACANT'
        WHERE id = ?
    """, (bed_id,))

    db.commit()


# ==================================================
# AUTO VACATE BED ON STUDENT STATUS CHANGE
# ==================================================
def auto_vacate_bed_on_status_change(db, ledger_no: str, new_status: str):
    """
    Auto vacates bed when student status becomes non-ACTIVE.
    Safe: preserves history and frees bed.
    """
    if not new_status or new_status.strip().upper() == "ACTIVE":
        return

    ledger_no = ledger_no.strip()
    cur = db.cursor()

    # Find active allotment
    cur.execute("""
        SELECT id, bed_id
        FROM bed_allotments
        WHERE ledger_number = ?
          AND status = 'ALLOTTED'
        ORDER BY id DESC
        LIMIT 1
    """, (ledger_no,))
    row = cur.fetchone()
    if not row:
        return

    allot_id = row["id"]
    bed_id = row["bed_id"]

    # Vacate allotment
    cur.execute("""
        UPDATE bed_allotments
        SET status = 'VACATED',
            vacate_date = ?,
            vacate_reason = ?
        WHERE id = ?
    """, (
        today_str(),
        f"Auto vacated due to status change to {new_status}",
        allot_id
    ))

    # Mark bed VACANT again
    cur.execute("""
        UPDATE beds
        SET status = 'VACANT'
        WHERE id = ?
    """, (bed_id,))

    db.commit()


# ==================================================
# OCCUPANCY LIST (SAFE NAME COLUMN)
# ==================================================
def get_occupancy(db):
    """
    Returns current occupied list for occupancy page.
    If students.full_name doesn't exist, uses students.student_name.
    """
    cur = db.cursor()

    # ✅ Try full_name
    try:
        cur.execute("""
            SELECT
                f.floor_name,
                r.room_no,
                b.bed_no,
                a.ledger_number,
                s.full_name AS full_name,
                a.allot_date
            FROM bed_allotments a
            JOIN beds b ON b.id = a.bed_id
            JOIN rooms r ON r.id = b.room_id
            JOIN floors f ON f.id = r.floor_id
            LEFT JOIN students s ON s.ledger_no = a.ledger_number
            WHERE a.status = 'ALLOTTED'
            ORDER BY
              CASE f.floor_name
                WHEN 'Ground Floor' THEN 1
                WHEN 'First Floor' THEN 2
                WHEN 'Second Floor' THEN 3
                WHEN 'Third Floor' THEN 4
                ELSE 99
              END,
              CAST(r.room_no AS INTEGER),
              CAST(b.bed_no AS INTEGER)
        """)
        return cur.fetchall()

    except Exception:
        # ✅ Fallback to student_name
        cur.execute("""
            SELECT
                f.floor_name,
                r.room_no,
                b.bed_no,
                a.ledger_number,
                s.student_name AS full_name,
                a.allot_date
            FROM bed_allotments a
            JOIN beds b ON b.id = a.bed_id
            JOIN rooms r ON r.id = b.room_id
            JOIN floors f ON f.id = r.floor_id
            LEFT JOIN students s ON s.ledger_no = a.ledger_number
            WHERE a.status = 'ALLOTTED'
            ORDER BY
              CASE f.floor_name
                WHEN 'Ground Floor' THEN 1
                WHEN 'First Floor' THEN 2
                WHEN 'Second Floor' THEN 3
                WHEN 'Third Floor' THEN 4
                ELSE 99
              END,
              CAST(r.room_no AS INTEGER),
              CAST(b.bed_no AS INTEGER)
        """)
        return cur.fetchall()


# ==================================================
# HISTORY LIST (LEDGER BASED)
# ==================================================
def get_history(db, ledger_no: str):
    """
    Returns bed allotment history for one ledger.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT
            f.floor_name,
            r.room_no,
            b.bed_no,
            a.status,
            a.allot_date,
            a.vacate_date,
            a.vacate_reason
        FROM bed_allotments a
        JOIN beds b ON b.id = a.bed_id
        JOIN rooms r ON r.id = b.room_id
        JOIN floors f ON f.id = r.floor_id
        WHERE a.ledger_number = ?
        ORDER BY a.id DESC
    """, (ledger_no.strip(),))
    return cur.fetchall()


# ==================================================
# DIRECT ALLOT (Used by Dashboard/Other Modules)
# ==================================================
def allot_bed_direct(ledger_no: str, bed_id: int, db):
    """
    Used by dashboard_routes.py
    Keep it consistent.
    """
    allot_bed(db, ledger_no, bed_id)
