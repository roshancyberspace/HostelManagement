from flask import render_template, request
from datetime import date, timedelta
from modules.student_attendance import student_attendance_bp
from modules.student_attendance.analytics_services import (
    attendance_percentage_by_class,
    attendance_percentage_by_block,
    gatepass_trend,
    chronic_absentees
)

@student_attendance_bp.route("/analytics")
def analytics():
    today = date.today()
    start_date = request.args.get("start", (today - timedelta(days=7)).isoformat())
    end_date = request.args.get("end", today.isoformat())

    class_data = attendance_percentage_by_class(start_date, end_date)
    block_data = attendance_percentage_by_block(start_date, end_date)
    gatepass_data = gatepass_trend(start_date, end_date)
    chronic = chronic_absentees(start_date, end_date)

    return render_template(
        "student_attendance/analytics.html",
        start_date=start_date,
        end_date=end_date,
        class_data=class_data,
        block_data=block_data,
        gatepass_data=gatepass_data,
        chronic=chronic
    )
