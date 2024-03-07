from . import error_handling_bp
from flask import render_template, jsonify

@error_handling_bp.app_errorhandler(400)
def handle_400(error):
    # Return a custom 400 response
    return render_template('error_handling/400.html'), 400

@error_handling_bp.app_errorhandler(401)
def handle_401(error):
    # Handle login required with an HTML template
    return render_template('error_handling/401.html'), 401

@error_handling_bp.app_errorhandler(403)
def handle_403(error):
    # Handle insufficient permissions with an HTML template
    return render_template('error_handling/403.html'), 403

@error_handling_bp.app_errorhandler(404)
def handle_404(error):
    # Return a custom 404 response
    return render_template('error_handling/404.html'), 404