from . import error_handling_bp
from flask import flash, redirect, url_for, render_template


@error_handling_bp.app_errorhandler(400)
def handle_400(error):
    return render_template('/error_handling/400.html'), 400

@error_handling_bp.app_errorhandler(401)
def handle_401(error):
    return render_template('/error_handling/401.html'), 401

@error_handling_bp.app_errorhandler(403)
def handle_403(error):
    return render_template('/error_handling/403.html'), 403

@error_handling_bp.app_errorhandler(404)
def handle_404(error):
    return render_template('/error_handling/404.html'), 404
