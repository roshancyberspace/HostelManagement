from flask import Blueprint

master_feed_bp = Blueprint(
    'master_feed',
    __name__,
    template_folder='templates'
)
