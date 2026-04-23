from flask import Blueprint

student_master_bp = Blueprint(
    "student_master",
    __name__,
    template_folder="templates"
)
