import os
import re
from pathlib import Path

from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from models.db import get_db


ROLE_CATALOG = [
    ("SUPER_ADMIN", "Super Admin"),
    ("ADMIN", "Admin"),
    ("HOSTEL_SUPERINTENDENT", "Hostel Superintendent"),
    ("ACCOUNTANT", "Accountant"),
    ("RECEPTION", "Reception"),
    ("MESS_INCHARGE", "Mess Incharge"),
    ("LAUNDRY", "Washerman / Laundry"),
    ("BARBER", "Barber"),
    ("HOSTEL_INCHARGE", "Hostel Incharge"),
    ("PARENTS", "Parents"),
]


PERMISSION_CATALOG = [
    ("dashboard.view", "Dashboard"),
    ("system.view", "System Check"),
    ("master_feed.manage", "Master Feed"),
    ("coaching.manage", "Coaching"),
    ("academic_session.manage", "Academic Session"),
    ("students.manage", "Student Intake"),
    ("staff.manage", "Staff and Members"),
    ("student_profile.view", "Student Profile"),
    ("parent_portal.view", "Parent Portal"),
    ("pocket_money.manage", "Pocket Money"),
    ("attendance.manage", "Student Attendance"),
    ("student_permissions.manage", "Student Permissions"),
    ("gate_pass.manage", "Gate Pass"),
    ("calendar_rules.manage", "Calendar Rules"),
    ("school_timings.manage", "School Timings"),
    ("hostel_timetable.manage", "Hostel Timetable"),
    ("daily_schedule.view", "Daily Schedule"),
    ("laundry.manage", "Laundry"),
    ("barber.manage", "Barber and Grooming"),
    ("mess_menu.manage", "Mess and Menu"),
    ("hostel_structure.manage", "Hostel Structure"),
    ("bed_allotment.manage", "Bed Allotment"),
    ("inspection.manage", "Inspection"),
    ("stock.manage", "Stock and Assets"),
    ("reports.view", "Reports"),
    ("rbac.manage", "User and Permission Management"),
]


DEFAULT_ROLE_PERMISSIONS = {
    "SUPER_ADMIN": [key for key, _ in PERMISSION_CATALOG],
    "ADMIN": [
        "dashboard.view", "students.manage", "staff.manage", "student_profile.view",
        "attendance.manage", "student_permissions.manage", "gate_pass.manage",
        "inspection.manage", "stock.manage", "reports.view", "bed_allotment.manage",
        "hostel_structure.manage", "parent_portal.view", "pocket_money.manage",
        "daily_schedule.view",
    ],
    "HOSTEL_SUPERINTENDENT": [
        "dashboard.view", "system.view", "master_feed.manage", "coaching.manage",
        "academic_session.manage", "students.manage", "staff.manage",
        "student_profile.view", "parent_portal.view", "pocket_money.manage",
        "attendance.manage", "student_permissions.manage", "gate_pass.manage",
        "calendar_rules.manage", "school_timings.manage", "hostel_timetable.manage",
        "daily_schedule.view", "laundry.manage", "barber.manage", "mess_menu.manage",
        "hostel_structure.manage", "bed_allotment.manage", "inspection.manage",
        "stock.manage", "reports.view",
    ],
    "ACCOUNTANT": ["dashboard.view", "pocket_money.manage", "parent_portal.view", "reports.view"],
    "RECEPTION": ["dashboard.view", "students.manage", "gate_pass.manage", "staff.manage"],
    "MESS_INCHARGE": ["dashboard.view", "mess_menu.manage", "daily_schedule.view"],
    "LAUNDRY": ["dashboard.view", "laundry.manage"],
    "BARBER": ["dashboard.view", "barber.manage"],
    "HOSTEL_INCHARGE": [
        "dashboard.view", "gate_pass.manage", "inspection.manage",
        "attendance.manage", "student_profile.view", "daily_schedule.view",
    ],
    "PARENTS": ["parent_portal.view"],
}


ROLE_LANDING_PATHS = {
    "SUPER_ADMIN": "/",
    "ADMIN": "/",
    "HOSTEL_SUPERINTENDENT": "/",
    "ACCOUNTANT": "/pocket-money/",
    "RECEPTION": "/students/list",
    "MESS_INCHARGE": "/mess-menu/?day_type=WORKING",
    "LAUNDRY": "/laundry-register/",
    "BARBER": "/barber",
    "HOSTEL_INCHARGE": "/gate-pass",
    "PARENTS": "/parent-portal/wallet",
}


PERMISSION_LANDING_PATHS = {
    "dashboard.view": "/",
    "students.manage": "/students/list",
    "staff.manage": "/staff",
    "student_profile.view": "/student-profile",
    "parent_portal.view": "/parent-portal/wallet",
    "pocket_money.manage": "/pocket-money/",
    "attendance.manage": "/student-attendance/",
    "student_permissions.manage": "/student-permissions/",
    "gate_pass.manage": "/gate-pass",
    "mess_menu.manage": "/mess-menu/?day_type=WORKING",
    "laundry.manage": "/laundry-register/",
    "barber.manage": "/barber",
    "hostel_structure.manage": "/structure/hostel",
    "bed_allotment.manage": "/bed-allotment/allot",
    "inspection.manage": "/inspection/common",
    "stock.manage": "/stock/",
    "reports.view": "/reports/rooms",
    "rbac.manage": "/rbac/users",
}


PATH_PERMISSION_RULES = [
    ("/rbac/", "rbac.manage"),
    ("/auth/profile", "dashboard.view"),
    ("/system-check", "system.view"),
    ("/master-feed", "master_feed.manage"),
    ("/coaching", "coaching.manage"),
    ("/academic-session", "academic_session.manage"),
    ("/students", "students.manage"),
    ("/staff", "staff.manage"),
    ("/student-profile", "student_profile.view"),
    ("/parent-portal", "parent_portal.view"),
    ("/pocket-money", "pocket_money.manage"),
    ("/student-attendance", "attendance.manage"),
    ("/student-permissions", "student_permissions.manage"),
    ("/gate-pass", "gate_pass.manage"),
    ("/calendar-rules", "calendar_rules.manage"),
    ("/school-timings", "school_timings.manage"),
    ("/hostel-timetable", "hostel_timetable.manage"),
    ("/daily-schedule", "daily_schedule.view"),
    ("/laundry-routine", "laundry.manage"),
    ("/laundry-register", "laundry.manage"),
    ("/barber", "barber.manage"),
    ("/mess-menu", "mess_menu.manage"),
    ("/structure", "hostel_structure.manage"),
    ("/bed-allotment", "bed_allotment.manage"),
    ("/inspection", "inspection.manage"),
    ("/inspection-alerts", "inspection.manage"),
    ("/stock", "stock.manage"),
    ("/reports", "reports.view"),
    ("/mismatch-active-without-bed", "reports.view"),
    ("/vacant-rooms", "reports.view"),
    ("/", "dashboard.view"),
]


PUBLIC_PATH_PREFIXES = ("/auth/login", "/static/")


def init_rbac_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS rbac_roles (
            role_key TEXT PRIMARY KEY,
            role_label TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS rbac_permissions (
            permission_key TEXT PRIMARY KEY,
            permission_label TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_key TEXT NOT NULL,
            permission_key TEXT NOT NULL,
            PRIMARY KEY (role_key, permission_key),
            FOREIGN KEY (role_key) REFERENCES rbac_roles(role_key) ON DELETE CASCADE,
            FOREIGN KEY (permission_key) REFERENCES rbac_permissions(permission_key) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS app_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role_key TEXT NOT NULL,
            profile_image TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_key) REFERENCES rbac_roles(role_key)
        )
        """
    )

    cur.executemany(
        "INSERT OR IGNORE INTO rbac_roles (role_key, role_label) VALUES (?, ?)",
        ROLE_CATALOG,
    )
    cur.executemany(
        "INSERT OR IGNORE INTO rbac_permissions (permission_key, permission_label) VALUES (?, ?)",
        PERMISSION_CATALOG,
    )

    for role_key, permissions in DEFAULT_ROLE_PERMISSIONS.items():
        existing = cur.execute(
            "SELECT COUNT(*) AS count FROM role_permissions WHERE role_key = ?",
            (role_key,),
        ).fetchone()["count"]
        if existing:
            continue
        cur.executemany(
            "INSERT OR IGNORE INTO role_permissions (role_key, permission_key) VALUES (?, ?)",
            [(role_key, permission_key) for permission_key in permissions],
        )

    user_count = cur.execute("SELECT COUNT(*) AS count FROM app_users").fetchone()["count"]
    if user_count == 0:
        cur.execute(
            """
            INSERT INTO app_users (user_id, full_name, password_hash, role_key, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (
                "superadmin",
                "Super Admin",
                generate_password_hash("admin123"),
                "SUPER_ADMIN",
            ),
        )

    conn.commit()
    conn.close()


def get_role_map():
    return {row["role_key"]: row["role_label"] for row in list_roles()}


def get_permission_map():
    return {row["permission_key"]: row["permission_label"] for row in _list_permission_rows()}


def get_user_permissions(role_key):
    conn = get_db()
    rows = conn.execute(
        "SELECT permission_key FROM role_permissions WHERE role_key = ? ORDER BY permission_key",
        (role_key,),
    ).fetchall()
    conn.close()
    return [row["permission_key"] for row in rows]


def fetch_user_by_user_id(user_id):
    conn = get_db()
    row = conn.execute(
        """
        SELECT u.*, r.role_label
        FROM app_users u
        JOIN rbac_roles r ON r.role_key = u.role_key
        WHERE u.user_id = ?
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return row


def fetch_user_by_id(user_pk):
    conn = get_db()
    row = conn.execute(
        """
        SELECT u.*, r.role_label
        FROM app_users u
        JOIN rbac_roles r ON r.role_key = u.role_key
        WHERE u.id = ?
        """,
        (user_pk,),
    ).fetchone()
    conn.close()
    return row


def build_session_user(user_row):
    if not user_row:
        return None
    permissions = get_user_permissions(user_row["role_key"])
    return {
        "id": user_row["id"],
        "user_id": user_row["user_id"],
        "name": user_row["full_name"],
        "role": user_row["role_key"],
        "role_label": user_row["role_label"],
        "profile_image": user_row["profile_image"],
        "permissions": permissions,
    }


def authenticate_user(user_id, password):
    user = fetch_user_by_user_id(user_id)
    if not user or not user["is_active"]:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    return build_session_user(user)


def refresh_session_user():
    user = session.get("user")
    if not user or not user.get("id"):
        return None
    fresh = fetch_user_by_id(user["id"])
    if not fresh or not fresh["is_active"]:
        session.pop("user", None)
        return None
    built = build_session_user(fresh)
    session["user"] = built
    return built


def get_current_user():
    return session.get("user")


def has_permission(permission_key, user=None):
    current = user or get_current_user()
    if not current:
        return False
    if current.get("role") == "SUPER_ADMIN":
        return True
    return permission_key in set(current.get("permissions", []))


def can_access_path(path, user=None):
    if not path:
        return False
    for prefix in PUBLIC_PATH_PREFIXES:
        if path.startswith(prefix):
            return True
    current = user or get_current_user()
    if not current:
        return False
    if path == "/auth/profile" or path.startswith("/auth/profile/"):
        return True
    if current.get("role") == "SUPER_ADMIN":
        return True
    for prefix, permission_key in PATH_PERMISSION_RULES:
        if path == prefix or path.startswith(f"{prefix}/"):
            return has_permission(permission_key, current)
    return True


def list_users():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT u.id, u.user_id, u.full_name, u.role_key, r.role_label, u.profile_image, u.is_active
        FROM app_users u
        JOIN rbac_roles r ON r.role_key = u.role_key
        ORDER BY u.full_name, u.user_id
        """
    ).fetchall()
    conn.close()
    return rows


def list_roles():
    conn = get_db()
    rows = conn.execute(
        "SELECT role_key, role_label FROM rbac_roles ORDER BY role_label"
    ).fetchall()
    conn.close()
    return rows


def list_permissions():
    return [
        {"key": row["permission_key"], "label": row["permission_label"]}
        for row in _list_permission_rows()
    ]


def _list_permission_rows():
    conn = get_db()
    rows = conn.execute(
        "SELECT permission_key, permission_label FROM rbac_permissions ORDER BY permission_label"
    ).fetchall()
    conn.close()
    return rows


def get_role_permissions_map():
    conn = get_db()
    rows = conn.execute(
        "SELECT role_key, permission_key FROM role_permissions ORDER BY role_key, permission_key"
    ).fetchall()
    conn.close()
    permission_map = {}
    for row in rows:
        permission_map.setdefault(row["role_key"], set()).add(row["permission_key"])
    return permission_map


def update_role_permissions(role_key, permission_keys):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM role_permissions WHERE role_key = ?", (role_key,))
    cur.executemany(
        "INSERT INTO role_permissions (role_key, permission_key) VALUES (?, ?)",
        [(role_key, permission_key) for permission_key in permission_keys],
    )
    conn.commit()
    conn.close()


def _normalize_key(value, suffix=""):
    key = (value or "").strip().upper()
    key = re.sub(r"[^A-Z0-9]+", "_", key).strip("_")
    if suffix and key and not key.endswith(suffix):
        key = f"{key}{suffix}"
    return key


def create_role(form):
    role_label = (form.get("role_label") or "").strip()
    role_key = _normalize_key(form.get("role_key") or role_label)

    if not role_key or not role_label:
        return False, "Role key and label are required."

    conn = get_db()
    existing = conn.execute(
        "SELECT 1 FROM rbac_roles WHERE role_key = ?",
        (role_key,),
    ).fetchone()
    if existing:
        conn.close()
        return False, "Role key already exists."

    conn.execute(
        "INSERT INTO rbac_roles (role_key, role_label) VALUES (?, ?)",
        (role_key, role_label),
    )
    conn.commit()
    conn.close()
    return True, "Role created successfully."


def update_role(role_key, form):
    role_label = (form.get("role_label") or "").strip()
    if not role_label:
        return False, "Role label is required."

    conn = get_db()
    cur = conn.execute(
        "UPDATE rbac_roles SET role_label = ? WHERE role_key = ?",
        (role_label, role_key),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return False, "Role not found."
    return True, "Role updated successfully."


def create_permission(form):
    permission_label = (form.get("permission_label") or "").strip()
    permission_key = (form.get("permission_key") or "").strip().lower()
    permission_key = re.sub(r"[^a-z0-9.]+", "_", permission_key).strip("_.")

    if not permission_key or not permission_label:
        return False, "Permission key and label are required."

    conn = get_db()
    existing = conn.execute(
        "SELECT 1 FROM rbac_permissions WHERE permission_key = ?",
        (permission_key,),
    ).fetchone()
    if existing:
        conn.close()
        return False, "Permission key already exists."

    conn.execute(
        "INSERT INTO rbac_permissions (permission_key, permission_label) VALUES (?, ?)",
        (permission_key, permission_label),
    )
    conn.commit()
    conn.close()
    return True, "Permission created successfully."


def update_permission(permission_key, form):
    permission_label = (form.get("permission_label") or "").strip()
    if not permission_label:
        return False, "Permission label is required."

    conn = get_db()
    cur = conn.execute(
        "UPDATE rbac_permissions SET permission_label = ? WHERE permission_key = ?",
        (permission_label, permission_key),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return False, "Permission not found."
    return True, "Permission updated successfully."


def get_landing_path(user):
    if not user:
        return "/auth/login"
    role_path = ROLE_LANDING_PATHS.get(user.get("role"))
    if role_path and can_access_path(role_path, user):
        return role_path
    for permission_key in user.get("permissions", []):
        path = PERMISSION_LANDING_PATHS.get(permission_key)
        if path and can_access_path(path, user):
            return path
    return "/"


def _save_profile_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    profile_dir = Path("static") / "uploads" / "profile_images"
    profile_dir.mkdir(parents=True, exist_ok=True)
    safe_name = secure_filename(file_storage.filename)
    target_name = f"profile_{safe_name}"
    target_path = profile_dir / target_name
    counter = 1
    while target_path.exists():
        target_name = f"profile_{counter}_{safe_name}"
        target_path = profile_dir / target_name
        counter += 1
    file_storage.save(target_path)
    return str(target_path).replace("\\", "/").replace("static/", "", 1)


def create_user(form, files):
    user_id = (form.get("user_id") or "").strip()
    full_name = (form.get("full_name") or "").strip()
    password = (form.get("password") or "").strip()
    role_key = (form.get("role_key") or "").strip()
    is_active = 1 if form.get("is_active") else 0

    if not user_id or not full_name or not password or not role_key:
        return False, "User ID, full name, password, and role are required."

    existing = fetch_user_by_user_id(user_id)
    if existing:
        return False, "User ID already exists."

    profile_image = _save_profile_image(files.get("profile_image"))

    conn = get_db()
    conn.execute(
        """
        INSERT INTO app_users (user_id, full_name, password_hash, role_key, profile_image, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            full_name,
            generate_password_hash(password),
            role_key,
            profile_image,
            is_active,
        ),
    )
    conn.commit()
    conn.close()
    return True, "User created successfully."


def update_user(user_pk, form, files):
    existing = fetch_user_by_id(user_pk)
    if not existing:
        return False, "User not found."

    user_id = (form.get("user_id") or "").strip()
    full_name = (form.get("full_name") or "").strip()
    password = (form.get("password") or "").strip()
    role_key = (form.get("role_key") or "").strip()
    is_active = 1 if form.get("is_active") else 0

    if not user_id or not full_name or not role_key:
        return False, "User ID, full name, and role are required."

    duplicate = fetch_user_by_user_id(user_id)
    if duplicate and duplicate["id"] != user_pk:
        return False, "Another user already uses this User ID."

    profile_image = existing["profile_image"]
    uploaded = _save_profile_image(files.get("profile_image"))
    if uploaded:
        profile_image = uploaded

    password_hash = existing["password_hash"]
    if password:
        password_hash = generate_password_hash(password)

    conn = get_db()
    conn.execute(
        """
        UPDATE app_users
        SET user_id = ?, full_name = ?, password_hash = ?, role_key = ?, profile_image = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            user_id,
            full_name,
            password_hash,
            role_key,
            profile_image,
            is_active,
            user_pk,
        ),
    )
    conn.commit()
    conn.close()
    return True, "User updated successfully."


def update_own_profile(user_pk, form, files):
    existing = fetch_user_by_id(user_pk)
    if not existing:
        return False, "User not found."

    full_name = (form.get("full_name") or "").strip()
    current_password = form.get("current_password") or ""
    new_password = (form.get("new_password") or "").strip()
    confirm_password = (form.get("confirm_password") or "").strip()

    if not full_name:
        return False, "Full name is required."

    password_hash = existing["password_hash"]
    if new_password or confirm_password:
        if not current_password:
            return False, "Current password is required to change password."
        if not check_password_hash(existing["password_hash"], current_password):
            return False, "Current password is incorrect."
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters."
        if new_password != confirm_password:
            return False, "New password and confirm password do not match."
        password_hash = generate_password_hash(new_password)

    profile_image = existing["profile_image"]
    uploaded = _save_profile_image(files.get("profile_image"))
    if uploaded:
        profile_image = uploaded

    conn = get_db()
    conn.execute(
        """
        UPDATE app_users
        SET full_name = ?, password_hash = ?, profile_image = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (full_name, password_hash, profile_image, user_pk),
    )
    conn.commit()
    conn.close()
    return True, "Profile updated successfully."
