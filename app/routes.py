import logging
from datetime import  datetime
import pytz
from sqlalchemy import func, case
from flask import Blueprint, request, jsonify, redirect, url_for, send_file, abort
from flask_login import login_required
from . import db, socketio
from .models import Customer, Order, Weight
# from .utils.helper import calculate_salmon_box
from .utils.pdf_utils import generate_delivery_note
# from app.utils.auth_decorators import permission_required, role_required


bp = Blueprint('_main', __name__)


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

    return redirect(url_for('order.order_detail', order_id=weight.order_id))



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

