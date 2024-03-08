from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, logout_user, login_user
from werkzeug.security import check_password_hash
from ... import login_manager
from ...models import User
from . import auth_bp


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
                flash("Login successful!" , 'success')
                return redirect(url_for('main.index'))
            elif user and not check_password_hash(user.password, password):
                flash("Wrong password! Please contact admin to change it!", 'error')
                return redirect(url_for('auth.login'))
            elif not user:
                flash("User not exist! Please contact admin!", 'error')
                return redirect(url_for('auth.login'))
        except ValueError:
            flash("Something went wrong! Please contact admin or try again later!", 'error')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout successful!" , 'info')
    return redirect(url_for('auth.login'))
