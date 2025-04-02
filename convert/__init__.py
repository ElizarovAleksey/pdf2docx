from flask import Blueprint

convert_bp = Blueprint('convert', __name__, template_folder='templates')

from . import routes
