from flask import request, send_file, abort
from flask_login import login_required
from ...utils.pdf_utils import generate_delivery_note
from ...utils.auth_decorators import permission_required, roles_required
from . import deliverynote_bp

@deliverynote_bp.route('/generate', methods=['GET'])
@roles_required('admin', 'driver', 'cutter')
def generate_pdf():
    date = request.args.get('date')
    customer = request.args.get('customer')
    pdf_file_path = generate_delivery_note(date, customer)
    if pdf_file_path:
        return send_file(pdf_file_path, as_attachment=True)
    else:
        abort(404)