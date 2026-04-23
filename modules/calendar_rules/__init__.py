from flask import Blueprint

calendar_rules_bp = Blueprint(
    "calendar_rules",
    __name__,
    template_folder="templates"
)
