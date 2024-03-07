from functools import wraps
from flask import flash, redirect, url_for, current_app, abort
from flask_login import current_user


# def permission_required(permission):
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             role_permissions = current_app.config.get('ROLE_PERMISSIONS', {})
#             if not current_user.is_authenticated:
#                 flash('Please log in to access this page.')
#                 return redirect(url_for('auth.login'))
            
#             if permission not in role_permissions.get(current_user.role, []):
#                 flash("You don't have permission to access this resource.", 'danger')
#                 return redirect(url_for('main.index'))
#             return f(*args, **kwargs)
#         return decorated_function
#     return decorator


# def role_required(role):
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             # First check if the user is authenticated
#             if not current_user.is_authenticated:
#                 flash('Please log in to access this page.')
#                 return redirect(url_for('auth.login'))
            
#             # Then check if the user has the required role
#             if current_user.role != role:
#                 flash('You do not have permission to view this page.')
#                 return redirect(url_for('main.index'))
#             return f(*args, **kwargs)
#         return decorated_function
#     return decorator

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            role_permissions = current_app.config.get('ROLE_PERMISSIONS', {})
            print(current_user.role)
            print(role_permissions)
            print(permission)
            print(current_user.is_authenticated)

            if not current_user.is_authenticated:
                print(401)
                abort(401)  # Use abort to raise an Unauthorized error
            if permission not in role_permissions.get(current_user.role, []):
                print(403)
                abort(403)  # Use abort to raise a Forbidden error
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized access
            if current_user.role != role:
                abort(403)  # Forbidden access
            return f(*args, **kwargs)
        return decorated_function
    return decorator