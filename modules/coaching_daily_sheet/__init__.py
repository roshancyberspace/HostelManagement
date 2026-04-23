from flask import Blueprint

coaching_daily_sheet_bp = Blueprint(
    "coaching_daily_sheet",
    __name__,
    template_folder="templates"
)

from . import routes
