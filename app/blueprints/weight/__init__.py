from flask import Blueprint

weight_bp = Blueprint('weight', __name__)

from . import views