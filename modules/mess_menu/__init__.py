from flask import Blueprint

mess_menu_bp = Blueprint(
    "mess_menu",
    __name__,
    template_folder="templates"
)
