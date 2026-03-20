from flask import Blueprint

traceability_bp = Blueprint("traceability", __name__)

from . import views
