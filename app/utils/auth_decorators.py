from functools import wraps
from flask import flash, redirect, url_for, current_app, abort
from flask_login import current_user


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            role_permissions = current_app.config.get('ROLE_PERMISSIONS', {})
            if not current_user.is_authenticated:
                abort(401)  # Use abort to raise an Unauthorized error
            if permission not in role_permissions.get(current_user.role, []):
                abort(403)  # Use abort to raise a Forbidden error
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized access
            if not hasattr(current_user, 'role') or current_user.role not in roles:
                abort(403)  # Forbidden access
            return f(*args, **kwargs)
        return decorated_function
    return decorator