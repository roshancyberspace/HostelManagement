from flask import Blueprint

academic_session_bp = Blueprint(
    "academic_session",
    __name__,
    template_folder="templates"
)
