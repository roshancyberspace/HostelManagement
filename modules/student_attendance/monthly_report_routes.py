from datetime import date, timedelta
from flask import render_template, request
from modules.student_attendance import student_attendance_bp
from modules.student_attendance.monthly_report_services import (
    get_previous_month_range,
    monthly_attendance_summary,
    monthly_chronic_absentees
)

@student_attendance_bp.route("/monthly-report", methods=["GET"])
def monthly_report():
    month_value = request.args.get("month", "")

    if month_value:
        selected = date.fromisoformat(f"{month_value}-01")
        start_date = selected.replace(day=1)
        if selected.month == 12:
            end_date = selected.replace(year=selected.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = selected.replace(month=selected.month + 1, day=1) - timedelta(days=1)
    else:
        start_date, end_date = get_previous_month_range()
        month_value = start_date.strftime("%Y-%m")

    summary = monthly_attendance_summary(start_date, end_date)
    chronic = monthly_chronic_absentees(start_date, end_date)

    return render_template(
        "student_attendance/monthly_report.html",
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        chronic=chronic,
        month_value=month_value
    )
