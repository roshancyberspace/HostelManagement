from flask import Blueprint

student_profile_bp = Blueprint(
    "student_profile",
    __name__,
    template_folder="templates"
)

from . import routes
