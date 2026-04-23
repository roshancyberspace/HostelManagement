from flask import Blueprint

hostel_timetable_bp = Blueprint(
    "hostel_timetable",
    __name__,
    template_folder="templates"
)
