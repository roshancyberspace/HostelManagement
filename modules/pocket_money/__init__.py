from flask import Blueprint

pocket_money_bp = Blueprint(
    "pocket_money",
    __name__,
    template_folder="templates"
)

from . import routes
