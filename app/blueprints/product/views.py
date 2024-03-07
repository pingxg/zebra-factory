from flask import jsonify
from flask_login import login_required
from . import product_bp
from ...models import Product
from ...utils.auth_decorators import permission_required

@product_bp.route('/get-active-products')
@login_required
def get_active_products():
    products = Product.get_active_products()
    return jsonify([product.product_name for product in products])