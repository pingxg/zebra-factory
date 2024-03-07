from flask import Blueprint

deliverynote_bp = Blueprint('deliverynote', __name__)

from . import views