from flask import request, jsonify, flash
from flask_login import login_required
from ... import socketio
from . import print_bp
from ...utils.auth_decorators import permission_required, roles_required


@print_bp.route('/emit_print_zebra', methods=['POST'])
@roles_required('admin', 'cutter')
def emit_print_zebra():
    data = request.json
    order_id = data.get('order_id')
    socketio.emit('print_zebra', {'order_id': order_id})
    flash('Print zebra event emitted','success')
    return jsonify({'status': 'Print zebra event emitted'})

