from flask import jsonify
from . import product_bp
from ...models import Product


@product_bp.route('/get-active-products')
def get_active_products():
    products = Product.get_active_products()
    return jsonify([product.product_name for product in products])