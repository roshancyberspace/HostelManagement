from flask import Blueprint

student_permissions_bp = Blueprint(
    "student_permissions",
    __name__,
    template_folder="templates"
)
