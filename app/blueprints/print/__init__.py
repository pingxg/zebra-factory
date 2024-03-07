from flask import Blueprint

print_bp = Blueprint('print', __name__)

from . import views