from flask import Blueprint

school_timings_bp = Blueprint(
    "school_timings",
    __name__,
    template_folder="templates"
)
