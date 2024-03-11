from . import error_handling_bp
from flask import flash, redirect, url_for, render_template

# @error_handling_bp.app_errorhandler(400)
# def handle_400(error):
#     flash('Bad request. Please try again!', 'error')
#     return redirect(url_for('main.index'))

# @error_handling_bp.app_errorhandler(401)
# def handle_401(error):
#     flash('You must be logged in to view this page!', 'error')
#     return redirect(url_for('auth.login'))

# @error_handling_bp.app_errorhandler(403)
# def handle_403(error):
#     flash('You do not have permission!', 'error')
#     return redirect(url_for('main.index'))

# @error_handling_bp.app_errorhandler(404)
# def handle_404(error):
#     flash('Page not found. The URL may be incorrect!', 'error')
#     return redirect(url_for('main.index'))


@error_handling_bp.app_errorhandler(400)
def handle_400(error):
    # flash('Bad request. Please try again!', 'error')
    return render_template('/error_handling/400.html'), 400

@error_handling_bp.app_errorhandler(401)
def handle_401(error):
    # flash('You must be logged in to view this page!', 'error')
    return render_template('/error_handling/401.html'), 401

@error_handling_bp.app_errorhandler(403)
def handle_403(error):
    # flash('You do not have permission!', 'error')
    return render_template('/error_handling/403.html'), 403

@error_handling_bp.app_errorhandler(404)
def handle_404(error):
    # flash('Page not found. The URL may be incorrect!', 'error')
    return render_template('/error_handling/404.html'), 404
