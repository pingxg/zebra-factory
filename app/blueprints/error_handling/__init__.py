from flask import Blueprint, jsonify, render_template

error_handling_bp = Blueprint('error_handling', __name__)


from . import views