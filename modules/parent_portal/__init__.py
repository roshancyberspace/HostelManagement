from flask import Blueprint

parent_portal_bp = Blueprint(
    "parent_portal",
    __name__,
    template_folder="templates",
    url_prefix="/parent"
)

from . import routes
