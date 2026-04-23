from flask import Flask, flash, redirect, request, session, url_for
from config import SECRET_KEY
from models.db import get_db
from services.rbac import can_access_path, get_current_user, get_landing_path, has_permission, init_rbac_tables, refresh_session_user

# -----------------------------
# CREATE APP
# -----------------------------
app = Flask(__name__)
app.secret_key = SECRET_KEY
init_rbac_tables()


# -----------------------------
# AUTH + ACCESS CONTROL
# -----------------------------
@app.before_request
def enforce_authentication():
    public_paths = ("/auth/login", "/static/")
    if request.path == "/":
        return None

    if request.path.startswith(public_paths):
        return None

    current_user = refresh_session_user()
    if not current_user:
        return redirect(url_for("auth.login", next=request.path))

    if not can_access_path(request.path, current_user):
        flash("You do not have permission to access this section.", "danger")
        return redirect(get_landing_path(current_user))


# -----------------------------
# CONTEXT PROCESSORS
# -----------------------------
from routes import inject_notifications
app.context_processor(inject_notifications)


@app.context_processor
def inject_rbac_helpers():
    return {
        "current_user": get_current_user(),
        "can": has_permission,
    }


# -----------------------------
# GLOBAL BED MISMATCH ALERT
# (LOGIN-TIME + PAGE LOAD)
# -----------------------------
@app.context_processor
def global_bed_mismatch_alert():
    """
    Shows alert if ACTIVE students exist without bed allotment.
    Visible only to SUPERINTENDENT.
    """
    if "user" not in session or not has_permission("reports.view"):
        return {}

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT COUNT(*) AS mismatch
        FROM students
        WHERE status = 'ACTIVE'
          AND ledger_no NOT IN (
              SELECT ledger_number
              FROM bed_allotments
              WHERE status = 'ALLOTTED'
          )
    """)

    count = cur.fetchone()["mismatch"]
    db.close()

    return {
        "global_bed_mismatch": count
    }


# -----------------------------
# IMPORT BLUEPRINTS
# -----------------------------
from routes.dashboard_routes import dashboard_bp
from routes.auth_routes import auth_bp, rbac_bp
from routes.structure_routes import structure_bp
from routes.inspection_routes import inspection_bp
from routes.stock_routes import stock_bp
from routes.report_routes import report_bp

from modules.master_feed.routes import master_feed_bp
from modules.academic_session.routes import academic_session_bp
from modules.calendar_rules.routes import calendar_rules_bp
from modules.school_timings.routes import school_timings_bp
from modules.hostel_timetable.routes import hostel_timetable_bp
from modules.mess_menu.routes import mess_menu_bp
from modules.daily_schedule.routes import daily_schedule_bp
from modules.laundry_routine.routes import laundry_routine_bp
from modules.laundry_register.routes import laundry_register_bp
from modules.student_master.routes import student_master_bp
from modules.student_permissions.routes import student_permissions_bp
from modules.student_attendance import student_attendance_bp
from modules.hostel_governance import hostel_governance_bp
from modules.student_profile import student_profile_bp
from modules.gate_pass.routes import gate_pass_bp
from modules.pocket_money import pocket_money_bp
from modules.parent_portal import parent_portal_bp
from modules.staff_management import staff_management_bp

# ✅ NEW MODULES
from modules.coaching_daily_sheet import coaching_daily_sheet_bp
from modules.barber_haircut import barber_haircut_bp

# ✅ ✅ BED ALLOTMENT (MISSING BEFORE)
from modules.bed_allotment.routes import bed_allotment_bp
from routes.room_inspection_routes import room_inspection_bp

# -----------------------------
# REGISTER BLUEPRINTS
# -----------------------------
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(rbac_bp)
app.register_blueprint(structure_bp)
app.register_blueprint(inspection_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(report_bp)

app.register_blueprint(master_feed_bp, url_prefix="/master-feed")
app.register_blueprint(academic_session_bp, url_prefix="/academic-session")
app.register_blueprint(calendar_rules_bp, url_prefix="/calendar-rules")
app.register_blueprint(school_timings_bp, url_prefix="/school-timings")
app.register_blueprint(hostel_timetable_bp, url_prefix="/hostel-timetable")
app.register_blueprint(mess_menu_bp, url_prefix="/mess-menu")
app.register_blueprint(daily_schedule_bp, url_prefix="/daily-schedule")
app.register_blueprint(laundry_routine_bp, url_prefix="/laundry-routine")
app.register_blueprint(laundry_register_bp, url_prefix="/laundry-register")
app.register_blueprint(student_master_bp, url_prefix="/students")
app.register_blueprint(student_permissions_bp, url_prefix="/student-permissions")

# These already have prefixes inside their own modules
app.register_blueprint(student_attendance_bp)
app.register_blueprint(hostel_governance_bp)
app.register_blueprint(student_profile_bp)
app.register_blueprint(gate_pass_bp)
app.register_blueprint(pocket_money_bp, url_prefix="/pocket-money")
app.register_blueprint(parent_portal_bp, url_prefix="/parent-portal")
app.register_blueprint(staff_management_bp)

# ✅ Coaching Daily Sheet
app.register_blueprint(coaching_daily_sheet_bp)
app.register_blueprint(barber_haircut_bp)

# ✅ ✅ Bed Allotment (NOW ACTIVE)
app.register_blueprint(bed_allotment_bp, url_prefix="/bed-allotment")
app.register_blueprint(room_inspection_bp)

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
