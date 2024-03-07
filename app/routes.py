import os
import logging
from collections import defaultdict
import numpy as np
from datetime import date, datetime, timedelta
import pytz
from sqlalchemy import func, case
from flask import Blueprint, render_template, request, jsonify, redirect, session, url_for, send_file, abort
from flask_login import login_required
from . import db, socketio
from .models import Customer, Order, Weight, Product, MaterialInfo
from .utils.date_utils import calculate_current_iso_week
from .utils.helper import calculate_salmon_box
from .utils.pdf_utils import generate_delivery_note
# from app.utils.auth_decorators import permission_required, role_required


bp = Blueprint('main', __name__)


# Set up logging with timestamp
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


@login_required
@socketio.on('keepalive')
def emit_keepalive_response(data):
    status = {'status': 'online'}  # Prepare the status information
    socketio.emit('keepalive_response', {})
    logger.info("Keep alive message reveiced from client, sending response.")



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

    if selected_date:
        order_details = (
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
                Product.product_type,
                case(
                    [(func.length(Order.fish_size) == 0, Customer.fish_size),  # If Order.fish_size is empty, use Customer.fish_size
                    (func.length(Customer.fish_size) == 0, Order.fish_size)],  # If Customer.fish_size is empty, use Order.fish_size
                    else_=func.coalesce(Order.fish_size, Customer.fish_size)
                ).label("fish_size")
            )
            .outerjoin(Product, Order.product == Product.product_name)
            .outerjoin(Weight, Order.id == Weight.order_id)
            .filter(Order.date == selected_date)
            .group_by(Order.id)
            .outerjoin(Customer, Order.customer == Customer.customer)
            .order_by(Customer.priority.asc(), Customer.packing.asc(), Order.product.asc(), "fish_size")
            .all()
        )
        grouped_orders = {}
        totals = {}  # Dictionary to store the total for each product group
        details = {}
        for order in order_details:
            if order[9] not in grouped_orders:
                grouped_orders[order[9]] = {}
            if f'Priority {order[7]}' not in grouped_orders[order[9]]:
                grouped_orders[order[9]][f'Priority {order[7]}'] = []
            grouped_orders[order[9]][f'Priority {order[7]}'].append(order)

            if order[3] not in totals:
                totals[order[3]] = []
                totals[order[3]].append(0)
                totals[order[3]].append(0)
            totals[order[3]][0] += (order[5])
            totals[order[3]][1] += (order[6])

        
            if order[9] == 'Lohi':

                key_name = f'{order[8]} | {order[3]} | {order[10]}'
                if key_name not in details.keys():
                    details[key_name] = np.array([[0, 0], [0, 0]])
                box_info_total = np.array(calculate_salmon_box(order[5]))
                # print(key_name, box_info_total)
                # else:
                #     details[key_name] = details[key_name] + np.array([box_info_total, [0, 0]])

                if float(order[6]) < float(order[5])*float(os.environ.get('COMPLETION_THRESHOLD', 0.9)):
                    box_info_unfinished = np.array(calculate_salmon_box(float(order[5])))
                    details[key_name] = details[key_name] + np.vstack([box_info_total, box_info_unfinished])
                else:
                    details[key_name] = details[key_name] + np.vstack([box_info_total, [0, 0]])

        totals = {key: totals[key] for key in sorted(totals)}
        details = {key: details[key] for key in sorted(details)}
        # print(details)
        # Preprocess data
        grouped_details = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for key, value in details.items():
            box_type, product_type, size = key.split(' | ')
            grouped_details[box_type][product_type][size] = value.tolist()

        # Flatten the structure and calculate row spans
        data_for_template = []
        category_rowspan_tracker = {}

        # Iterate through categories and subcategories
        for category, subcategories in grouped_details.items():
            category_rowspan = sum(len(items) for items in subcategories.values())
            category_rowspan_tracker[category] = category_rowspan
            for subcategory, items in subcategories.items():
                subcategory_rowspan = len(items)
                category_subcategory_unique = f"{category}_{subcategory}"
                for item, values in items.items():
                    row = {
                        "category": category,
                        "subcategory": subcategory,
                        "item": item,
                        "full_total": values[0][0],
                        "half_total": values[0][1],
                        "full_unfinished": values[1][0],
                        "half_unfinished": values[1][1],
                        "merge_info": {
                            "category_rowspan": category_rowspan_tracker.get(category, 0),
                            "subcategory_rowspan": subcategory_rowspan,
                            "category_subcategory_unique": category_subcategory_unique
                        }
                    }
                    # Append row to data list
                    data_for_template.append(row)
                # After processing the first item of a subcategory, subsequent items should not repeat the subcategory name
                subcategory_rowspan = 0
            # Reset category rowspan tracker for this category after processing
            category_rowspan_tracker[category] = 0
        grouped_orders = {k: v for k, v in sorted(grouped_orders.items())}

    return render_template('main/index.html', grouped_orders=grouped_orders, selected_date=selected_date, totals=totals, grouped_details=grouped_details, data_for_template=data_for_template, timedelta=timedelta)


@bp.route('/order/<int:order_id>', methods=['GET', 'POST'])
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

        weight = Weight(
            order_id=order_id, 
            quantity=scale_reading, 
            production_time=datetime.now(pytz.timezone(os.environ.get('TIMEZONE'))),
            batch_number=batch_number
            )
        db.session.add(weight)
        db.session.commit()
        session['show_toast'] = True
        return redirect(url_for('main.order_detail', order_id=order_id))

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

    return render_template('orders/order_detail.html', order=order, show_toast=show_toast, weight_details=weight_details)


@bp.route('/weight/<int:weight_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_weight(weight_id):
    weight = Weight.query.filter_by(id=weight_id).first()
    
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
    weight = Weight.query.filter_by(id=weight_id).first()
    if not weight:
        return "Weight not found", 404

    db.session.delete(weight)
    db.session.commit()

    return redirect(url_for('main.order_detail', order_id=weight.order_id))


@bp.route('/order', methods=['GET', 'POST'])
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
    return render_template('orders/order.html', week_str=week_str, orders_by_customer=orders_by_customer, week_dates=week_dates)


@bp.route('/download-delivery-note')
@login_required
def download_delivery_note():
    date = request.args.get('date')
    customer = request.args.get('customer')
    pdf_file_path = generate_delivery_note(date, customer)
    if pdf_file_path:
        return send_file(pdf_file_path, as_attachment=True)
    else:
        abort(404)


@bp.route('/get-order-info/<int:order_id>')
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


@bp.route('/add-order', methods=['GET', 'POST'])
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

@bp.route('/update-order/<int:order_id>', methods=['POST'])
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


@bp.route('/delete-order/<int:order_id>', methods=['DELETE'])
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


@bp.route('/api/customers')
def get_customers():
    customers = Customer.query.filter(Customer.active == 1).order_by(Customer.customer.asc()).all()
    return jsonify([customer.customer for customer in customers])

@bp.route('/api/products')
def get_products():
    products = Product.query.filter(Product.active == 1).order_by(Product.product_name.asc()).all()
    return jsonify([product.product_name for product in products])

@bp.route('/api/fish-sizes')
def get_fish_sizes():
    # Query distinct fish_size values
    fish_sizes = Customer.query.with_entities(Customer.fish_size).distinct().order_by(Customer.fish_size.asc()).all()
    fish_sizes = [size[0] for size in fish_sizes if size[0] is not None and size[0] != '']  # Convert to list and filter out None
    return jsonify(fish_sizes)
