from flask import Blueprint

gate_pass_bp = Blueprint(
    "gate_pass",
    __name__,
    template_folder="templates"
)
