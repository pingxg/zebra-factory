# from flask import Flask, render_template, request, jsonify
# from flask_socketio import SocketIO

# app = Flask(__name__)
# socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for simplicity

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         data = request.form.get('data')
#         # Emit a 'print' event to any connected client
#         socketio.emit('print', {'data': data})
#         return jsonify({'status': 'sent'})
#     return render_template('index.html')



from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import mysql.connector
from datetime import date
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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
    selected_customer = request.form.get('selected_customer')

    # Fetch distinct customers for the selected date
    cursor.execute("SELECT DISTINCT customer FROM orders WHERE date = %s", (selected_date,))
    customers = cursor.fetchall()

    order_details = None
    if selected_customer:
        cursor.execute("SELECT details FROM orders WHERE date = %s AND customer = %s", (selected_date, selected_customer))
        order_details = cursor.fetchone()

    return render_template('index.html', order=order_details, customers=customers, selected_date=selected_date)

@socketio.on('new_order_added')
def handle_new_order(data):
    # When a new order is added, notify all connected clients
    emit('refresh_data', {'message': 'A new order has been added!'}, broadcast=True)



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)