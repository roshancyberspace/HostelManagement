from flask import Blueprint

laundry_routine_bp = Blueprint(
    "laundry_routine",
    __name__,
    template_folder="templates"
)
