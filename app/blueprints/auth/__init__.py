from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

# Import the views after initializing the blueprint to avoid circular imports
from . import views


