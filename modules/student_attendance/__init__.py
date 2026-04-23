from flask import Blueprint

student_attendance_bp = Blueprint(
    "student_attendance",
    __name__,
    template_folder="templates",
    url_prefix="/attendance"
)

from . import routes
from . import analytics_routes
from . import monthly_report_routes
from . import pdf_routes
