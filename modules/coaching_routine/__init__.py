from flask import Blueprint

coaching_routine_bp = Blueprint(
    'coaching_routine',
    __name__,
    template_folder='templates'
)

from . import routes
