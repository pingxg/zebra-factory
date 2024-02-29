from flask import Blueprint, render_template, request, jsonify, redirect, session, url_for, flash, send_file, make_response, abort
from flask_login import login_required, logout_user, login_user
from werkzeug.security import check_password_hash
from .models import User, Customer, Order, OrderWeight, ProductName, MaterialInfo
from . import db, login_manager, socketio
import os
from datetime import date, datetime, timedelta
from collections import defaultdict
from sqlalchemy import func, case
import pytz
import re
from pdfrw import PdfReader, PdfWriter
import shutil
import threading
import time
import numpy as np
import logging
from xhtml2pdf import pisa

from pprint import pprint as pp

bp = Blueprint('main', __name__)


# Set up logging with timestamp
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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


@login_required
@socketio.on('keepalive')
def emit_keepalive_response(data):
    status = {'status': 'online'}  # Prepare the status information
    socketio.emit('keepalive_response', {})
    logger.info("Keep alive message reveiced from client, sending response.")


@bp.context_processor
def inject_global_vars():
    return dict(completion_threshold=os.environ.get('COMPLETION_THRESHOLD', 0.9),
                completion_threshold_upper=os.environ.get('COMPLETION_THRESHOLD_UPPER', 1.3))


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
                (func.coalesce(func.sum(OrderWeight.quantity), 0)).label("total_produced"),
                Customer.priority,
                Customer.packing,
                ProductName.product_type,
                case(
                    [(func.length(Order.fish_size) == 0, Customer.fish_size),  # If Order.fish_size is empty, use Customer.fish_size
                    (func.length(Customer.fish_size) == 0, Order.fish_size)],  # If Customer.fish_size is empty, use Order.fish_size
                    else_=func.coalesce(Order.fish_size, Customer.fish_size)
                ).label("fish_size")
            )
            .outerjoin(ProductName, Order.product == ProductName.product_name)
            .outerjoin(OrderWeight, Order.id == OrderWeight.order_id)
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

    return render_template('index.html', grouped_orders=grouped_orders, selected_date=selected_date, totals=totals, grouped_details=grouped_details, data_for_template=data_for_template,timedelta=timedelta)


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
            print(int(batch_number[0]))

        weight = OrderWeight(
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

    return render_template('order_detail.html', order=order, show_toast=show_toast, weight_details=weight_details)


@bp.route('/weight/<int:weight_id>/edit', methods=['GET', 'POST'])
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

@bp.route('/weight/<int:weight_id>/delete', methods=['POST'])
@login_required
def delete_weight(weight_id):
    weight = OrderWeight.query.filter_by(id=weight_id).first()
    if not weight:
        return "Weight not found", 404

    db.session.delete(weight)
    db.session.commit()

    return redirect(url_for('main.order_detail', order_id=weight.order_id))


@bp.route('/order-editing', methods=['GET', 'POST'])
@login_required
def order_editing():
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
    return render_template('order_editing.html', week_str=week_str, orders_by_customer=orders_by_customer, week_dates=week_dates)


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


def generate_delivery_note(date, customer=None):
    # Utility function
    def convert_html_to_pdf(source_html, output_filename):
        # open output file for writing (truncated binary)
        with open(output_filename, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(
                    source_html,
                    dest=result_file)
        return pisa_status.err
    data = get_data_for_pdf(date, customer)

    if os.path.exists(os.path.join(os.getcwd(), "temp")):
        # Remove the directory and all its contents
        shutil.rmtree(os.path.join(os.getcwd(), "temp"))

    if not os.path.exists(os.path.join(os.getcwd(), "temp")):
        os.makedirs(os.path.join(os.getcwd(), "temp"))
    
    if data:
        for i in range(len(data)):
            html_content = render_template('salmon_delivery_template.html', data=data[i])
            pdf_file_name = f"{date}_{customer}.pdf" if customer else f"{date}_{i:03d}.pdf"
            pdf_file_path = os.path.join(os.getcwd(), "temp", pdf_file_name)
            convert_html_to_pdf(html_content, pdf_file_path)
        matching_files = []
        if customer is None:
            # Regular expression pattern to match 'yyyy-mm-dd_{index}'
            pattern = r'^\d{4}-\d{2}-\d{2}_\d+.pdf$'
            # List to store matching file paths
            
            # Iterate through files in the directory
            for filename in os.listdir("temp" ):
                if re.match(pattern, filename):
                    full_path = os.path.join("temp", filename)
                    matching_files.append(full_path)
                    matching_files.append(full_path)

            pdf_file_name = f"{date}.pdf"
        else:
            matching_files.append(os.path.join("temp", pdf_file_name))
            matching_files.append(os.path.join("temp", pdf_file_name))

        writer = PdfWriter()
        pdf_file_path = os.path.join(os.getcwd(), "temp", pdf_file_name)
        for inpfn in sorted(matching_files):
            writer.addpages(PdfReader(inpfn).pages)
        writer.write(pdf_file_path)

        
    else:
        return False
    return pdf_file_path



def get_data_for_pdf(date, customer=None):

    subquery = (
        db.session.query(
            OrderWeight.order_id,
            func.coalesce(func.sum(OrderWeight.quantity), 0).label("delivered")
        )
        .group_by(OrderWeight.order_id)
        .subquery()
    )

    query = db.session.query(
        Order.customer.label("store"), 
        Customer.company.label("customer"),
        Customer.address,
        Customer.phone,
        Order.date,
        Order.product,
        (func.coalesce(Order.price * 1.14, 0)).label("price"),
        Order.quantity.label("weight"),
        subquery.c.delivered,
    )\
    .outerjoin(subquery, Order.id == subquery.c.order_id) \
    .outerjoin(Customer, Order.customer == Customer.customer)\
    .filter(Order.date == date)\
    .order_by(Order.customer.asc(), Order.product.asc())

    # Apply customer filter if customer is provided
    if customer:
        query = query.filter(Customer.customer == customer)

    # Finalize the query
    data = query.all()

    store_dict = defaultdict(lambda: {
        'store': '',
        'customer': '',
        'address': '',
        'phone': '',
        'date': '',
        'order_detail': [],
        'contain_frozen':False,
        'contain_lohi':False,
        'contain_other':False,
    })

    for order in data:
        store, customer, address, phone, date, product, price, weight, delivered = order

        # Convert Decimal and datetime.date to a more friendly format if necessary
        price = float(price) if price is not None else 0.0
        weight = float(weight) if weight is not None else 0.0
        delivered = float(delivered) if delivered is not None else 0.0
        date = date.strftime('%Y-%m-%d')

        if store not in store_dict:
            store_dict[store].update({
                'store': store,
                'customer': customer,
                'address': address,
                'phone': phone,
                'date': date
            })

        store_dict[store]['order_detail'].append({
            'id': len(store_dict[store]['order_detail']) + 1,
            'product': product,
            'weight': str(round(weight,2)),
            'price': str(round(price,2)),
            'delivered': str(round(delivered,2))
        })
        if 'Frozen' in product:
            store_dict[store]['contain_frozen'] = True
        elif 'Frozen' not in product and 'Lohi' in product:
            store_dict[store]['contain_lohi'] = True
        elif 'Lohi' not in product:
            store_dict[store]['contain_other'] = True

    return list(store_dict.values())

def calculate_salmon_box(amount, threshold=2):
    full_box, half_box = 0, 0
    # Convert amount to a float for simplicity
    amount = float(amount)
    if amount <= 0:
        full_box, half_box = 0, 0

    if amount < 10:
        full_box, half_box = 0, 1
    
    if amount == 10:
        full_box, half_box = 1, 0
    
    # Check if amount is divisible by 10
    if amount % 10 == 0:
        full_box, half_box = amount / 10, 0
    
    # If not divisible by 10, check the threshold
    lower_bound = amount - (amount % 10)  # Lower multiple of 10
    if (amount - lower_bound) <= threshold:
        full_box, half_box = lower_bound / 10, 0
    else:
        full_box, half_box = lower_bound / 10, 1

    return [int(full_box), int(half_box)]



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
        print(order)
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
    return jsonify({'status': 'success', 'message': 'Order added successfully'})


@bp.route('/update-order/<int:order_id>', methods=['POST'])
@login_required
def update_order(order_id):
    data = request.json
    print(data)
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



def calculate_current_iso_week():
    # Get the current date
    current_date = datetime.now()

    # Calculate the start and end of the current ISO week
    # ISO weeks start on Monday and end on Sunday
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Format the dates to match the `input[type=week]` value format (YYYY-W##)
    # Where ## is the ISO week number
    week_number = current_date.isocalendar()[1]
    year = start_of_week.year

    # Pad the week number with leading zero if necessary
    week_number_str = f"{week_number:02d}"

    # Combine into the full string
    week_range_str = f"{year}-W{week_number_str}"

    return week_range_str

