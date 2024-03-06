# app/blueprints/orders/views.py
from flask import render_template, request, redirect, url_for, flash
# from . import orders_bp  # Import the Blueprint instance
from flask import Blueprint, render_template, request, jsonify, redirect, session, url_for, flash, send_file, make_response, abort
from flask_login import login_required
from ...models import Customer, Order, OrderWeight, ProductName, MaterialInfo
from datetime import date, datetime, timedelta
from ... import db, socketio
import os
import pytz
from sqlalchemy import func, case
from . import orders_bp  # Import the Blueprint instance
from collections import defaultdict
from ...utils.date_utils import calculate_current_iso_week

@orders_bp.route('/order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def order_detail(order_id):
    if request.method == 'POST':
        scale_reading = float(request.form['scale_reading'])
        batch_number = request.form['batch_number']
        try:
            batch_number = int(batch_number)
        except:
            print("Batch number not provided")
            batch_number = (
                db.session.query(
                    MaterialInfo.batch_number, 
                )
                .order_by(MaterialInfo.date.desc())
                .first()
            )

        weight = OrderWeight(
            order_id=order_id, 
            quantity=scale_reading, 
            production_time=datetime.now(pytz.timezone(os.environ.get('TIMEZONE'))),
            batch_number=batch_number
            )
        db.session.add(weight)
        db.session.commit()
        session['show_toast'] = True
        return redirect(url_for('orders.order_detail', order_id=order_id))

    show_toast = session.pop('show_toast', False)

    # Using SQLAlchemy ORM to retrieve the order with total produced and weight details
    order = (
        db.session.query(
            Order.id, 
            Order.customer, 
            Order.date, 
            Order.product,
            (func.coalesce(Order.price * 1.14, 0)).label("price"),
            Order.quantity,
            (func.coalesce(func.sum(OrderWeight.quantity), 0)).label("total_produced"),
            Customer.priority,
            Customer.packing,
            case(
                [(func.length(Order.fish_size) == 0, Customer.fish_size),  # If Order.fish_size is empty, use Customer.fish_size
                (func.length(Customer.fish_size) == 0, Order.fish_size)],  # If Customer.fish_size is empty, use Order.fish_size
                else_=func.coalesce(Order.fish_size, Customer.fish_size)
            ).label("fish_size")
        )
        .outerjoin(OrderWeight, Order.id == OrderWeight.order_id)
        .filter(Order.id == order_id)
        .group_by(Order.id)
        .outerjoin(Customer, Order.customer == Customer.customer)
        .first()
    )
    weight_details = (
        db.session.query(OrderWeight.id, OrderWeight.quantity, OrderWeight.production_time)
        .filter(OrderWeight.order_id == order_id)
        .order_by(OrderWeight.production_time.asc())
        .all()
    )

    if not order:
        return "Order not found", 404

    return render_template('orders/order_detail.html', order=order, show_toast=show_toast, weight_details=weight_details)



@orders_bp.route('/weight/<int:weight_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_weight(weight_id):
    weight = OrderWeight.query.filter_by(id=weight_id).first()
    
    if not weight:
        return jsonify(success=False, error="Weight not found"), 404

    if request.method == 'POST':
        edit_val = request.form.get('edit_weight')
        weight.quantity = edit_val
        db.session.commit()
        return jsonify(success=True)

@orders_bp.route('/weight/<int:weight_id>/delete', methods=['POST'])
@login_required
def delete_weight(weight_id):
    weight = OrderWeight.query.filter_by(id=weight_id).first()
    if not weight:
        return "Weight not found", 404

    db.session.delete(weight)
    db.session.commit()

    return redirect(url_for('orders.order_detail', order_id=weight.order_id))


@orders_bp.route('/order', methods=['GET', 'POST'])
@login_required
def order():
    week_str = request.args.get('week', calculate_current_iso_week())

    year, week = map(int, week_str.split('-W'))
    start_date = date.fromisocalendar(year, week, 1)
    end_date = start_date + timedelta(days=7)

    # Check if prev_week or next_week buttons were clicked
    if 'prev_week' in request.args:
        start_date -= timedelta(weeks=1)
    elif 'next_week' in request.args:
        start_date += timedelta(weeks=1)
    end_date = start_date + timedelta(days=7)


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
            (func.coalesce(func.sum(OrderWeight.quantity), 0)).label("total_produced"),
        )
        .filter(Order.date.between(start_date, end_date))
        .outerjoin(OrderWeight, Order.id == OrderWeight.order_id)
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
    return render_template('orders/order.html', week_str=week_str, orders_by_customer=orders_by_customer, week_dates=week_dates)



@orders_bp.route('/get-order-info/<int:order_id>')
@login_required
def get_order_info(order_id):
    # Retrieve order from database
    order = (
        db.session.query(
            Order.id, 
            Order.customer, 
            Order.date, 
            Order.product,
            (func.coalesce(Order.price * 1.14, 0)).label("price"),
            Order.quantity,
            case(
                [(func.length(Order.fish_size) == 0, Customer.fish_size),
                (func.length(Customer.fish_size) == 0, Order.fish_size)],
                else_=func.coalesce(Order.fish_size, Customer.fish_size)
            ).label("fish_size")
        )
        .join(Customer, Order.customer == Customer.customer)
        .filter(Order.id == order_id)
        .first()
    )
    if order:
        # Manually mapping the selected columns to their values
        order_dict = {
            "id": order.id,
            "customer": order.customer,
            "date": order.date.isoformat(),
            "product": order.product,
            "price": order.price,
            "quantity": order.quantity,
            "fish_size": order.fish_size,
            "original_price": order.price,
            "original_quantity": order.quantity,
            "original_fish_size": order.fish_size,
        }
        return jsonify(order_dict)
    else:
        return jsonify({"error": "Order not found"}), 404


@orders_bp.route('/add-order', methods=['GET', 'POST'])
@login_required
def add_order():
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    # Create a new instance of the Order model with the data from the request
    try:
        new_order = Order(
            customer=data['customer'],
            product=data['product'],
            price=float(data['price'])/1.14,  # Assuming the price needs to be adjusted
            quantity=float(data['quantity']),
            fish_size=data['fishSize'] if 'fishSize' in data else None,
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        )
        # Add the new order to the session and commit it to the database
        db.session.add(new_order)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Order added successfully'})

    except Exception as e:
        # Rollback in case of error
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@orders_bp.route('/update-order/<int:order_id>', methods=['POST'])
@login_required
def update_order(order_id):
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    if request.method == 'POST':
        if not order_id:
            return jsonify({'status': 'error', 'message': 'Order ID not provided'}), 400

        # Fetch the order from the database
        order = Order.query.filter_by(id=order_id).first()

        if order:
            order.price = data['price']/1.14
            order.quantity = data['quantity']
            order.fish_size = data['fish_size']
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Order updated successfully', 'order_id': order_id})
        else:
            return jsonify({'status': 'error', 'message': 'Order not found'}), 404


@orders_bp.route('/delete-order/<int:order_id>', methods=['DELETE'])
@login_required
def delete_order(order_id):
    if not order_id:
        return jsonify({'status': 'error', 'message': 'Order ID not provided'}), 400

    # Delete the order from the database
    order = Order.query.filter_by(id=order_id).first()
    if order:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Order deleted successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Order not found'}), 404


# This import statement should be at the bottom to avoid circular imports
from app.blueprints.orders import orders_bp

