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
    'autocommit':True,

}
cnx = mysql.connector.connect(**db_config)
# cursor = cnx.cursor()

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_date = request.form.get('selected_date', date.today())  # Default to today's date

    order_details = None
    if selected_date:
        query = """
	    SELECT o.id, o.customer, o.date, o.product, COALESCE(o.price * 1.14, 0) AS price, o.quantity, COALESCE(SUM(w.quantity), 0) AS total_produced
        FROM salmon_orders o
        LEFT JOIN salmon_order_weight w ON o.id = w.order_id
        WHERE o.date = %s
        GROUP BY o.id, o.customer, o.date, o.product, o.price, o.quantity
        """
        # query = "SELECT * FROM salmon_orders WHERE date = %s"
        # cursor.execute(,(selected_date,))
        # cursor.execute(query,(selected_date,))
        # order_details = cursor.fetchall()
        # cursor.close()
        with cnx.cursor() as cursor:
            cursor.execute(query,(selected_date,))
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


@app.route('/order/<int:order_id>', methods=['GET', 'POST'])
def order_detail(order_id):
    show_toast = False

    if request.method == 'POST':
        scale_reading = float(request.form['scale_reading'])
        query = "INSERT INTO salmon_order_weight (order_id, quantity, production_time) VALUES (%s, %s, %s)"


        with cnx.cursor() as cursor:
            cursor.execute(query,(order_id, scale_reading, datetime.now(pytz.timezone(os.environ.get('time_zone')))))
            order_with_total_produced = cursor.fetchall()
            cnx.commit()
        show_toast = True

    # Query to join salmon_orders with salmon_order_weight to get total produced amount and order details
    query = """
        SELECT o.id, o.customer, o.date, o.product, COALESCE(o.price * 1.14, 0) AS price, o.quantity, COALESCE(SUM(w.quantity), 0) AS total_produced
        FROM salmon_orders o
        LEFT JOIN salmon_order_weight w ON o.id = w.order_id
        WHERE o.id = %s
        GROUP BY o.id, o.customer, o.date, o.product, o.price, o.quantity
    """

    weight_detail_query = "SELECT id, quantity, production_time FROM salmon_order_weight WHERE order_id = %s ORDER BY production_time ASC"


    with cnx.cursor() as cursor:
        cursor.execute(query, (order_id,))
        order_with_total_produced = cursor.fetchall()
        cursor.execute(weight_detail_query, (order_id,))
        weight_details = cursor.fetchall()




    if not order_with_total_produced:
        return "Order not found", 404


    return render_template('order_detail.html', order=order_with_total_produced, show_toast=show_toast, weight_details=weight_details)




if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)