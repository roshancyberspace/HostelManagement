from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DB = BASE_DIR / "hostel.db"
TARGET_DB = BASE_DIR / "hostel_fresh_login_settings_only.db"

# Keep only authentication, RBAC, and setup/configuration data.
PRESERVE_TABLES = {
    "academic_sessions",
    "app_users",
    "beds",
    "blocks",
    "calendar_rules",
    "common_area_items",
    "common_areas",
    "expected_rooms",
    "floors",
    "hostel_timetable",
    "hostels",
    "inspection_items_master",
    "laundry_routine_items",
    "laundry_weekly_routine",
    "master_forms",
    "master_routines",
    "mess_menu_items",
    "mess_menu_weekly",
    "rbac_permissions",
    "rbac_roles",
    "role_permissions",
    "room_items",
    "rooms",
    "school_timings",
}


def main() -> None:
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Source DB not found: {SOURCE_DB}")

    shutil.copy2(SOURCE_DB, TARGET_DB)

    conn = sqlite3.connect(TARGET_DB)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")

    tables = [
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]

    for table in tables:
        if table in PRESERVE_TABLES:
            continue
        cur.execute(f'DELETE FROM "{table}"')

    # Remove scratch/test tables if present.
    for table in tables:
        if table.startswith("__write_test"):
            cur.execute(f'DROP TABLE IF EXISTS "{table}"')

    # Normalize structure after deleting live occupancy/activity data.
    cur.execute("UPDATE beds SET status = 'VACANT'")
    cur.execute(
        """
        UPDATE rooms
        SET status = CASE
            WHEN UPPER(COALESCE(status, '')) = 'DAMAGED' THEN status
            WHEN UPPER(COALESCE(room_type, '')) IN ('OFFICE', 'VISITOR') THEN 'VACANT'
            ELSE 'ACTIVE'
        END,
        merged_into_room_id = NULL
        """
    )
    cur.execute(
        "UPDATE app_users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP",
        (generate_password_hash("admin123"),),
    )

    conn.commit()

    remaining = {}
    for table in sorted(PRESERVE_TABLES):
        if cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (table,)
        ).fetchone():
            remaining[table] = cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

    conn.close()

    print(f"Fresh DB created: {TARGET_DB}")
    for table, count in remaining.items():
        print(f"{table}\t{count}")


if __name__ == "__main__":
    main()
