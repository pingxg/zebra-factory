from flask import Blueprint

main_bp = Blueprint('/test', __name__)

# Import the views after initializing the blueprint to avoid circular imports
# from . import views


