from flask import Blueprint

barber_haircut_bp = Blueprint(
    "barber_haircut",
    __name__,
    template_folder="templates"
)

from . import routes
