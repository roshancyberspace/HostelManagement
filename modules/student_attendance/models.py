from models.db import db
from datetime import datetime

class StudentAttendance(db.Model):
    __tablename__ = "student_attendance"

    id = db.Column(db.Integer, primary_key=True)

    ledger_no = db.Column(db.String(50), nullable=False, index=True)

    attendance_date = db.Column(db.Date, nullable=False)
    day_type = db.Column(db.String(20), nullable=False)  
    # WORKING / HOLIDAY

    slot = db.Column(db.String(30), nullable=False)
    # MORNING / AFTERNOON_RETURN / COACHING / EVENING / NIGHT

    status = db.Column(db.String(20), nullable=False)
    # PRESENT / ABSENT / LEAVE / MEDICAL

    remarks = db.Column(db.Text, nullable=True)

    application_file = db.Column(db.String(255), nullable=True)

    is_gatepass = db.Column(db.Boolean, default=False)

    snapshot = db.Column(db.JSON, nullable=False)
    # hostel, block, floor, room, bed, class

    marked_by = db.Column(db.String(100), nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

    corrected = db.Column(db.Boolean, default=False)
    correction_reason = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint(
            "ledger_no",
            "attendance_date",
            "slot",
            name="unique_attendance_per_slot"
        ),
    )
@student_attendance_bp.route("/load", methods=["GET"])
def load_students():
    from datetime import date
    from modules.student_attendance.services import fetch_students_for_attendance

    att_date = date.fromisoformat(request.args["attendance_date"])
    slot = request.args["slot"]
    class_filter = request.args.get("class")

    filters = {}
    if class_filter:
        filters["class"] = class_filter

    students = fetch_students_for_attendance(filters)

    return render_template(
        "student_attendance/mark_attendance.html",
        attendance_date=att_date,
        slot=slot,
        students=students
    )
