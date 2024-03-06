from flask_login import login_required, logout_user, login_user
from werkzeug.security import check_password_hash
from ...models import User
from ... import login_manager
from flask import render_template, request, redirect,url_for, flash
from . import auth_bp

# Routes
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        try:
            # Check if user exists and password is correct
            if user and check_password_hash(user.password, password):
                remember_me = False
                if 'remember' in request.form and request.form.get('remember') == "on":
                    remember_me = True
                    login_user(user, remember=remember_me)
                else:
                    login_user(user)
                return redirect(url_for('main.index'))

            else:
                flash("Invalid email or password.", 'danger')
                return redirect(url_for('auth.login'))
        except ValueError:
            flash("Invalid email or password.", 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))