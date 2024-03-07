from flask import request, jsonify
from flask_login import login_required
from ... import socketio
from . import print_bp
from ...utils.auth_decorators import permission_required


@print_bp.route('/emit_print_zebra', methods=['POST'])
@permission_required('print_label')
def emit_print_zebra():
    data = request.json
    order_id = data.get('order_id')
    socketio.emit('print_zebra', {'order_id': order_id})
    return jsonify({'status': 'Print zebra event emitted'})

# Routes
@print_bp.route('/emit_print_pdf', methods=['POST'])
@permission_required('print_label')
@permission_required('download_delivery_note')
def emit_print_pdf():
    data = request.json
    order_id = data.get('order_id')
    socketio.emit('print_pdf', {'order_id': order_id})
    return jsonify({'status': 'Print pdf event emitted'})

