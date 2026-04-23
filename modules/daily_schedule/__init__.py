from flask import Blueprint

daily_schedule_bp = Blueprint(
    "daily_schedule",
    __name__,
    template_folder="templates"
)
