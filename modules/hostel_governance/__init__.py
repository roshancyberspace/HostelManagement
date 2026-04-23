from flask import Blueprint

hostel_governance_bp = Blueprint(
    "hostel_governance",
    __name__,
    template_folder="templates"
)

from . import routes
