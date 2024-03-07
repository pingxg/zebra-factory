from flask import jsonify
from flask_login import login_required
from ...utils.auth_decorators import permission_required
from . import customer_bp
from ...models import Customer

@customer_bp.route('/get-active-customers')
@login_required
def get_active_customers():
    customers = Customer.get_active_customers()
    return jsonify([customer.customer for customer in customers])

@customer_bp.route('/get-fish-sizes')
@login_required
def get_distinct_fish_sizes():
    fish_sizes = Customer.get_distinct_fish_sizes()
    return jsonify(fish_sizes)