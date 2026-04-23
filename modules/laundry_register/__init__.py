from flask import Blueprint

laundry_register_bp = Blueprint(
    "laundry_register",
    __name__,
    template_folder="templates"
)
