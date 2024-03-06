# app/blueprints/printing.py
from flask import Blueprint

printing_bp = Blueprint('printing', __name__)

from . import views
