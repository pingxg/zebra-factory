from functools import wraps
from flask import flash, redirect, url_for, current_app
from flask_login import current_user


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            role_permissions = current_app.config.get('ROLE_PERMISSIONS', {})
            if not current_user.is_authenticated:
                flash('Please log in to access this page.')
                return redirect(url_for('auth.login'))
            
            if permission not in role_permissions.get(current_user.role, []):
                flash("You don't have permission to access this resource.", 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check if the user is authenticated
            if not current_user.is_authenticated:
                flash('Please log in to access this page.')
                return redirect(url_for('auth.login'))
            
            # Then check if the user has the required role
            if current_user.role != role:
                flash('You do not have permission to view this page.')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator