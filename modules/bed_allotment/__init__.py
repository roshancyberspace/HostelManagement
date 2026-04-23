from flask import Blueprint

bed_allotment_bp = Blueprint(
    'bed_allotment',
    __name__,
    template_folder='templates',
    url_prefix='/bed'
)

from . import routes
