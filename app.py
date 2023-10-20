# Standard Libraries
import os
from datetime import date, datetime
from collections import defaultdict

# Third-party Libraries
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

import pytz
from dotenv import load_dotenv

# Configuration
load_dotenv()  # Load environment variables from .env
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('secret_key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Custom Jinja2 Filters
app.jinja_env.filters['float'] = float


# SQLAlchemy setup
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+mysqldb://{os.environ.get('db_user')}:{os.environ.get('db_password')}@"
    f"{os.environ.get('db_host')}:{os.environ.get('db_port')}/{os.environ.get('db_name')}?charset=utf8mb4"
)
app.config['SQLALCHEMY_POOL_SIZE'] = 15
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 10
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class SalmonOrder(db.Model):
    __tablename__ = "salmon_orders"
    
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String)
    date = db.Column(db.Date)
    product = db.Column(db.String)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    
    weights = db.relationship("SalmonOrderWeight", backref="order")


class SalmonOrderWeight(db.Model):
    __tablename__ = "salmon_order_weight"
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('salmon_orders.id'))
    quantity = db.Column(db.Float)
    production_time = db.Column(db.DateTime)


# Routes
@app.route('/emit_print_zebra', methods=['POST'])
def emit_print_zebra():
    data = request.json
    order_id = data.get('order_id')
    socketio.emit('print_zebra', {'order_id': order_id})
    return jsonify({'status': 'Print zebra event emitted'})

# Routes
@app.route('/emit_print_pdf', methods=['POST'])
def emit_print_pdf():
    data = request.json
    order_id = data.get('order_id')
    socketio.emit('print_pdf', {'order_id': order_id})
    return jsonify({'status': 'Print pdf event emitted'})



@app.route('/', methods=['GET', 'POST'])
def index():
    selected_date = request.form.get('selected_date', date.today())  # Default to today's date
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
                (func.coalesce(func.sum(SalmonOrderWeight.quantity), 0)).label("total_produced")
            )
            .outerjoin(SalmonOrderWeight, SalmonOrder.id == SalmonOrderWeight.order_id)
            .filter(SalmonOrder.date == selected_date)
            .group_by(SalmonOrder.id)
            .all()
        )
        grouped_orders = defaultdict(list)
        totals = {}  # Dictionary to store the total for each product group

        for order in order_details:
            grouped_orders[order[3]].append(order)
            if order[3] not in totals:
                totals[order[3]] = 0
            totals[order[3]] += int(order[5])

    return render_template('index.html', grouped_orders=grouped_orders, selected_date=selected_date, totals=totals)


@app.route('/order/<int:order_id>', methods=['GET', 'POST'])
def order_detail(order_id):
    if request.method == 'POST':
        scale_reading = float(request.form['scale_reading'])
        weight = SalmonOrderWeight(order_id=order_id, 
                                    quantity=scale_reading, 
                                    production_time=datetime.now(pytz.timezone(os.environ.get('time_zone'))))
        db.session.add(weight)
        db.session.commit()
        session['show_toast'] = True
        return redirect(url_for('order_detail', order_id=order_id))

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
            (func.coalesce(func.sum(SalmonOrderWeight.quantity), 0)).label("total_produced")
        )
        .outerjoin(SalmonOrderWeight, SalmonOrder.id == SalmonOrderWeight.order_id)
        .filter(SalmonOrder.id == order_id)
        .group_by(SalmonOrder.id)
        .first()
    )

    weight_details = (
        db.session.query(SalmonOrderWeight.id, SalmonOrderWeight.quantity, SalmonOrderWeight.production_time)
        .filter(SalmonOrderWeight.order_id == order_id)
        .order_by(SalmonOrderWeight.production_time.asc())
        .all()
    )

    if not order:
        return "Order not found", 404

    return render_template('order_detail.html', order=order, show_toast=show_toast, weight_details=weight_details)


@app.route('/weight/<int:weight_id>/edit', methods=['GET', 'POST'])
def edit_weight(weight_id):
    weight = SalmonOrderWeight.query.filter_by(id=weight_id).first()
    
    if not weight:
        return jsonify(success=False, error="Weight not found"), 404

    if request.method == 'POST':
        edit_val = request.form.get('edit_weight')
        weight.quantity = edit_val
        db.session.commit()
        return jsonify(success=True)

@app.route('/weight/<int:weight_id>/delete', methods=['POST'])
def delete_weight(weight_id):
    weight = SalmonOrderWeight.query.filter_by(id=weight_id).first()
    
    if not weight:
        return "Weight not found", 404

    db.session.delete(weight)
    db.session.commit()

    return redirect(url_for('order_detail', order_id=weight.order_id))


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)