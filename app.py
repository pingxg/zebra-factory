from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import mysql.connector
from datetime import date
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import defaultdict
import pytz

load_dotenv()  # take environment variables from .env.
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")



# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         data = request.form.get('data')
#         # Emit a 'print' event to any connected client
#         socketio.emit('print', {'data': data})
#         return jsonify({'status': 'sent'})
#     return render_template('index.html')



# Setup MySQL connection
db_config = {
    'user': os.environ.get('db_user'),
    'password': os.environ.get('db_password'),
    'host': os.environ.get('db_host'),
    'database': os.environ.get('db_name'),
    'port': os.environ.get('db_port'),

}
cnx = mysql.connector.connect(**db_config)
cursor = cnx.cursor()

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_date = request.form.get('selected_date', date.today())  # Default to today's date

    order_details = None
    if selected_date:
        cursor.execute("SELECT * FROM salmon_orders WHERE date = %s",(selected_date,))
        order_details = cursor.fetchall()
        grouped_orders = defaultdict(list)
        totals = {}  # Dictionary to store the total for each product group

        for order in order_details:
            grouped_orders[order[3]].append(order)
            if order[3] not in totals:
                totals[order[3]] = 0
            totals[order[3]] += int(order[5])
    return render_template('index.html', grouped_orders=grouped_orders, selected_date=selected_date, totals=totals)

@socketio.on('new_order_added')
def handle_new_order(data):
    # When a new order is added, notify all connected clients
    emit('refresh_data', {'message': 'A new order has been added!'}, broadcast=True)

# @app.route('/order/<int:order_id>', methods=['GET'])
# def order_detail(order_id):
#     # Fetch order details based on the provided order_id
#     cursor.execute("SELECT id, customer, date, product, COALESCE(price * 1.14, 0) AS price, quantity FROM salmon_orders WHERE id = %s", (order_id,))
#     order = cursor.fetchall()

#     if not order:
#         return "Order not found", 404

#     return render_template('order_detail.html', order=order)


@app.route('/order/<int:order_id>', methods=['GET', 'POST'])
def order_detail(order_id):
    show_toast = False

    if request.method == 'POST':
        scale_reading = float(request.form['scale_reading'])
        
        cursor.execute("INSERT INTO salmon_order_weight (order_id, quantity, production_time) VALUES (%s, %s, %s)", (order_id, scale_reading, datetime.now(pytz.timezone(os.environ.get('time_zone')))))
        cnx.commit()

        show_toast = True

    cursor.execute("SELECT id, customer, date, product, COALESCE(price * 1.14, 0) AS price, quantity FROM salmon_orders WHERE id = %s", (order_id,))
    order = cursor.fetchall()

    if not order:
        return "Order not found", 404

    return render_template('order_detail.html', order=order, show_toast=show_toast)




if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)