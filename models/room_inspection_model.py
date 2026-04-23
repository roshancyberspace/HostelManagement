from datetime import date


def today_str():
    return date.today().isoformat()


# ==================================================
# MASTER ITEMS
# ==================================================
def get_inspection_master_items(db):
    return db.execute("""
        SELECT id, item_name, category
        FROM inspection_items_master
        WHERE status='ACTIVE'
        ORDER BY category, item_name
    """).fetchall()


# ==================================================
# ONLY AC STUDENT ROOMS
# ==================================================
def get_ac_student_rooms(db):
    return db.execute("""
        SELECT r.id, r.room_no, f.floor_name
        FROM rooms r
        JOIN floors f ON f.id = r.floor_id
        WHERE UPPER(r.ac_type)='AC'
          AND r.bed_capacity > 0
        ORDER BY
          CASE f.floor_name
            WHEN 'Ground Floor' THEN 1
            WHEN 'First Floor' THEN 2
            WHEN 'Second Floor' THEN 3
            WHEN 'Third Floor' THEN 4
            ELSE 99
          END,
          CAST(r.room_no AS INTEGER)
    """).fetchall()


# ==================================================
# EXPECTED ITEMS (FROM room_items inventory)
# ==================================================
def get_room_expected_items(db, room_id):
    return db.execute("""
        SELECT item_name, SUM(quantity) AS qty
        FROM room_items
        WHERE room_id=?
        GROUP BY item_name
        ORDER BY item_name
    """, (room_id,)).fetchall()


# ==================================================
# COLUMN DETECTOR FOR room_inspections
# ==================================================
def _room_inspections_cols(db):
    cols = db.execute("PRAGMA table_info(room_inspections);").fetchall()
    return [c["name"] for c in cols]


def _has_col(db, colname: str) -> bool:
    return colname in _room_inspections_cols(db)


# ==================================================
# SAVE INSPECTION (AUTO-COMPATIBLE)
# ==================================================
def save_room_inspection(db, room_id, inspector_name, remarks, item_results):
    """
    item_results:
      [{item_id, condition, remarks}]
    """
    cur = db.cursor()

    cols = _room_inspections_cols(db)

    # Choose best available columns
    has_inspector = "inspector_name" in cols
    has_remarks = "remarks" in cols
    has_inspected_on = "inspected_on" in cols

    # Build dynamic insert
    insert_cols = ["room_id"]
    insert_vals = [int(room_id)]

    if has_inspected_on:
        insert_cols.append("inspected_on")
        insert_vals.append(today_str())

    if has_inspector:
        insert_cols.append("inspector_name")
        insert_vals.append(inspector_name or "")

    if has_remarks:
        insert_cols.append("remarks")
        insert_vals.append(remarks or "")

    placeholders = ",".join(["?"] * len(insert_cols))

    cur.execute(f"""
        INSERT INTO room_inspections ({",".join(insert_cols)})
        VALUES ({placeholders})
    """, tuple(insert_vals))

    inspection_id = cur.lastrowid

    # Insert inspection lines
    for r in item_results:
        cur.execute("""
            INSERT INTO room_inspection_lines (inspection_id, item_id, condition, remarks)
            VALUES (?, ?, ?, ?)
        """, (
            inspection_id,
            int(r["item_id"]),
            (r.get("condition") or "GOOD").strip().upper(),
            r.get("remarks", "")
        ))

    db.commit()
    return inspection_id


# ==================================================
# REPORT: LATEST ISSUES (AUTO SAFE)
# ==================================================
def get_latest_room_issues(db, limit=200):
    cols = _room_inspections_cols(db)

    inspector_select = "'' AS inspector_name"
    if "inspector_name" in cols:
        inspector_select = "i.inspector_name AS inspector_name"

    inspected_on_select = "'' AS inspected_on"
    if "inspected_on" in cols:
        inspected_on_select = "i.inspected_on AS inspected_on"

    return db.execute(f"""
        SELECT
            f.floor_name,
            r.room_no,
            m.item_name,
            l.condition,
            l.remarks,
            {inspected_on_select},
            {inspector_select}
        FROM room_inspection_lines l
        JOIN room_inspections i ON i.id = l.inspection_id
        JOIN rooms r ON r.id = i.room_id
        JOIN floors f ON f.id = r.floor_id
        JOIN inspection_items_master m ON m.id = l.item_id
        WHERE l.condition IN ('MISSING','DAMAGED')
        ORDER BY i.id DESC
        LIMIT ?
    """, (limit,)).fetchall()
