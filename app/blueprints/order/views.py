
import os
import pytz
from collections import defaultdict
from datetime import date, datetime, timedelta
from flask import render_template, request, jsonify, redirect, session, url_for
from flask_login import login_required
from sqlalchemy import func, case
from . import order_bp
from ... import db
from ...models import Order, Weight, MaterialInfo, Customer
from ...utils.date_utils import calculate_current_iso_week
from ...services.order_service import OrderService
from ...utils.auth_decorators import permission_required, role_required
from flask_login import current_user


@order_bp.route('/', methods=['GET', 'POST'])
@login_required
def order():
    week_str = request.args.get('week', calculate_current_iso_week())

    year, week = map(int, week_str.split('-W'))
    start_date = date.fromisocalendar(year, week, 1)
    end_date = start_date + timedelta(days=6)

    # Check if prev_week or next_week buttons were clicked
    if 'prev_week' in request.args:
        start_date -= timedelta(weeks=1)
    elif 'next_week' in request.args:
        start_date += timedelta(weeks=1)
    end_date = start_date + timedelta(days=6)


    # Update week_str to reflect the new week
    week_str = f"{start_date.year}-W{start_date.isocalendar()[1]:02d}"

    orders = (
        db.session.query(
            Order.id, 
            Order.customer,
            Order.date,
            Order.product,
            (func.coalesce(Order.price * 1.14, 0)).label("price"),
            Order.quantity,
            (func.coalesce(func.sum(Weight.quantity), 0)).label("total_produced"),
        )
        .filter(Order.date.between(start_date, end_date))
        .outerjoin(Weight, Order.id == Weight.order_id)
        .order_by(Order.customer.asc(), Order.product.asc())
        .group_by(Order.id)
        .all()
    )
    # Organize orders by customer and date
    orders_by_customer = defaultdict(lambda: defaultdict(list))
    for order in orders:
        orders_by_customer[order.customer][order.date].append(order)

    # List of dates in the week for column headers
    week_dates = [start_date + timedelta(days=i) for i in range(7)]
    return render_template('order/order.html', week_str=week_str, orders_by_customer=orders_by_customer, week_dates=week_dates)


@order_bp.route('/<int:order_id>', methods=['GET', 'POST'])
@login_required
def order_detail(order_id):
    # if request.method == 'POST':
    #     scale_reading = float(request.form['scale_reading'])
    #     batch_number = request.form['batch_number']
    #     try:
    #         batch_number = int(batch_number)
    #     except:
    #         print("Batch number not provided")
    #         batch_number = (
    #             db.session.query(
    #                 MaterialInfo.batch_number, 
    #             )
    #             .order_by(MaterialInfo.date.desc())
    #             .first()
    #         )

    #     weight = Weight(
    #         order_id=order_id, 
    #         quantity=scale_reading, 
    #         production_time=datetime.now(pytz.timezone(os.environ.get('TIMEZONE'))),
    #         batch_number=batch_number
    #         )
    #     db.session.add(weight)
    #     db.session.commit()
    #     session['show_toast'] = True
    #     return redirect(url_for('order.order_detail', order_id=order_id))

    # show_toast = session.pop('show_toast', False)

    order = (
        db.session.query(
            Order.id, 
            Order.customer, 
            Order.date, 
            Order.product,
            (func.coalesce(Order.price * 1.14, 0)).label("price"),
            Order.quantity,
            (func.coalesce(func.sum(Weight.quantity), 0)).label("total_produced"),
            Customer.priority,
            Customer.packing,
            case(
                [(func.length(Order.fish_size) == 0, Customer.fish_size),  # If Order.fish_size is empty, use Customer.fish_size
                (func.length(Customer.fish_size) == 0, Order.fish_size)],  # If Customer.fish_size is empty, use Order.fish_size
                else_=func.coalesce(Order.fish_size, Customer.fish_size)
            ).label("fish_size")
        )
        .outerjoin(Weight, Order.id == Weight.order_id)
        .filter(Order.id == order_id)
        .group_by(Order.id)
        .outerjoin(Customer, Order.customer == Customer.customer)
        .first()
    )
    weight_details = (
        db.session.query(Weight.id, Weight.quantity, Weight.production_time)
        .filter(Weight.order_id == order_id)
        .order_by(Weight.production_time.asc())
        .all()
    )
    if not order:
        return "Order not found", 404

    return render_template('order/order_detail.html', order=order, weight_details=weight_details)


@permission_required('edit_order')
@order_bp.route('/get/<int:order_id>', methods=['GET', 'POST'])
def get_order(order_id):
    if not order_id:
        return jsonify({'status': 'error', 'message': 'Order ID not provided'}), 400
    
    
    result = OrderService.get_order(order_id)
    return jsonify(result)

@permission_required('edit_order')
@order_bp.route('/add', methods=['POST'])
def add_order():
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    result = OrderService.add_order(data)
    return jsonify(result)

@permission_required('edit_order')
@order_bp.route('/update/<int:order_id>', methods=['POST'])
def update_order(order_id):
    data = request.json
    if not data or not order_id:
        return jsonify({'status': 'error', 'message': 'No data provided or Order ID missing'}), 400
    result = OrderService.update_order(order_id, data)
    return jsonify(result)


@permission_required('edit_order')
@order_bp.route('/delete/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    if not order_id:
        return jsonify({'status': 'error', 'message': 'Order ID not provided'}), 400
    result = OrderService.delete_order(order_id)
    return jsonify(result)
