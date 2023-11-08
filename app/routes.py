from flask import Blueprint, render_template, request, jsonify, redirect, session, url_for, flash
from flask_login import login_required, logout_user, login_user
from werkzeug.security import check_password_hash
from .models import User,Customer, SalmonOrder, SalmonOrderWeight
from . import db, login_manager, socketio
import os
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func
import pytz

bp = Blueprint('main', __name__)




# Routes
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        try:
            # Check if user exists and password is correct
            if user and check_password_hash(user.password, password):
                remember_me = False
                print(request.form.get('remember'))
                if 'remember' in request.form and request.form.get('remember') =="on":
                    remember_me = True
                    login_user(user, remember=remember_me)
                else:
                    login_user(user)
                return redirect(url_for('main.index'))

            else:
                flash("Invalid email or password.", 'danger')
                return redirect(url_for('main.login'))
        except ValueError:
            flash("Invalid email or password.", 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@bp.route('/emit_print_zebra', methods=['POST'])
@login_required
def emit_print_zebra():
    data = request.json
    order_id = data.get('order_id')
    socketio.emit('print_zebra', {'order_id': order_id})
    return jsonify({'status': 'Print zebra event emitted'})

# Routes
@bp.route('/emit_print_pdf', methods=['POST'])
@login_required
def emit_print_pdf():
    data = request.json
    order_id = data.get('order_id')
    socketio.emit('print_pdf', {'order_id': order_id})
    return jsonify({'status': 'Print pdf event emitted'})



@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # selected_date = request.form.get('selected_date') or request.args.get('selected_date', (datetime.today() + timedelta(days=1)).date())
    selected_date_str = request.form.get('selected_date') or request.args.get('selected_date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        # Default to tomorrow's date if none is provided
        selected_date = (datetime.today() + timedelta(days=1)).date()

    # Check if prev_date or next_date buttons were clicked
    if 'prev_date' in request.form:
        selected_date -= timedelta(days=1)
    elif 'next_date' in request.form:
        selected_date += timedelta(days=1)

    order_details = None
    if selected_date:
        order_details = (
            db.session.query(
                SalmonOrder.id, 
                SalmonOrder.customer, 
                SalmonOrder.date, 
                SalmonOrder.product,
                (func.coalesce(SalmonOrder.price * 1.14, 0)).label("price"),
                SalmonOrder.quantity,
                (func.coalesce(func.sum(SalmonOrderWeight.quantity), 0)).label("total_produced"),
                Customer.priority,
                Customer.packing,
            )
            .outerjoin(SalmonOrderWeight, SalmonOrder.id == SalmonOrderWeight.order_id)
            .filter(SalmonOrder.date == selected_date)
            .group_by(SalmonOrder.id)
            .outerjoin(Customer, SalmonOrder.customer == Customer.customer)
            .all()
        )
        grouped_orders = defaultdict(list)
        totals = {}  # Dictionary to store the total for each product group

        for order in order_details:
            grouped_orders[order[3]].append(order)
            if order[3] not in totals:
                totals[order[3]] = 0
            totals[order[3]] += int(order[5])

    return render_template('index.html', grouped_orders=grouped_orders, selected_date=selected_date, totals=totals, timedelta=timedelta)


@bp.route('/order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def order_detail(order_id):
    if request.method == 'POST':
        scale_reading = float(request.form['scale_reading'])
        weight = SalmonOrderWeight(order_id=order_id, 
                                    quantity=scale_reading, 
                                    production_time=datetime.now(pytz.timezone(os.environ.get('TIMEZONE'))))
        db.session.add(weight)
        db.session.commit()
        session['show_toast'] = True
        return redirect(url_for('main.order_detail', order_id=order_id))

    show_toast = session.pop('show_toast', False)

    # Using SQLAlchemy ORM to retrieve the order with total produced and weight details
    order = (
        db.session.query(
            SalmonOrder.id, 
            SalmonOrder.customer, 
            SalmonOrder.date, 
            SalmonOrder.product,
            (func.coalesce(SalmonOrder.price * 1.14, 0)).label("price"),
            SalmonOrder.quantity,
            (func.coalesce(func.sum(SalmonOrderWeight.quantity), 0)).label("total_produced"),
            Customer.priority,
            Customer.packing,

        )
        .outerjoin(SalmonOrderWeight, SalmonOrder.id == SalmonOrderWeight.order_id)
        .filter(SalmonOrder.id == order_id)
        .group_by(SalmonOrder.id)
        .outerjoin(Customer, SalmonOrder.customer == Customer.customer)
        .first()
    )

    weight_details = (
        db.session.query(SalmonOrderWeight.id, SalmonOrderWeight.quantity, SalmonOrderWeight.production_time)
        .filter(SalmonOrderWeight.order_id == order_id)
        .order_by(SalmonOrderWeight.production_time.asc())
        .all()
    )
    print(order)
    if not order:
        return "Order not found", 404

    return render_template('order_detail.html', order=order, show_toast=show_toast, weight_details=weight_details)


@bp.route('/weight/<int:weight_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_weight(weight_id):
    weight = SalmonOrderWeight.query.filter_by(id=weight_id).first()
    
    if not weight:
        return jsonify(success=False, error="Weight not found"), 404

    if request.method == 'POST':
        edit_val = request.form.get('edit_weight')
        weight.quantity = edit_val
        db.session.commit()
        return jsonify(success=True)

@bp.route('/weight/<int:weight_id>/delete', methods=['POST'])
@login_required
def delete_weight(weight_id):
    weight = SalmonOrderWeight.query.filter_by(id=weight_id).first()
    
    if not weight:
        return "Weight not found", 404

    db.session.delete(weight)
    db.session.commit()

    return redirect(url_for('main.order_detail', order_id=weight.order_id))