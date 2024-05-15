import os
import boto3
import uuid
import html
from botocore.client import Config
from datetime import datetime
from flask import request, send_file, abort, jsonify, flash, redirect, url_for
from flask_login import login_required
from ...utils.pdf_utils import generate_delivery_note
from ...utils.auth_decorators import permission_required, roles_required
from . import deliverynote_bp
from ... import db
from ...models import Order, DeliveryNoteImage

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

@deliverynote_bp.route('/get-presigned-post', methods=['POST'])
@roles_required('admin', 'driver')
def get_presigned_post():
    if request.method == 'POST':
        data = request.get_json()
        filename = data.get('filename')
        filetype = data.get('filetype')

        # Generate a unique key for the file
        key = f"uploads/{uuid.uuid4()}_{filename}"

        s3 = boto3.client('s3', config=Config(signature_version='s3v4'))

        # Specify the allowed file type and other conditions
        conditions = [
            {"Content-Type": filetype},  # Use the provided file type
            ["starts-with", "$key", "uploads/"]  # Files should be uploaded with a specific prefix
        ]

        # Generate the pre-signed POST
        post = s3.generate_presigned_post(
            Bucket=os.getenv('AWS_S3_BUCKET_NAME'),
            Key=key,
            Conditions=conditions,
            ExpiresIn=3600
        )

        # Return the pre-signed POST data
        return jsonify(post)


@deliverynote_bp.route('/update-image-links', methods=['POST'])
@roles_required('admin', 'driver')
def upload_images():
    data = request.get_json()
    customer_name = html.unescape(data.get('customer_name'))
    date_str = data.get('date')
    image_urls = data.get('image_urls')  # List of image URLs

    if not customer_name or not date_str or not image_urls:
        return jsonify({"error": "Missing data"}), 400

    # Convert date string to date object
    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Retrieve all orders for the given customer on the specified date
    orders = Order.query.filter_by(customer=customer_name, date=date).all()

    if not orders:
        return jsonify({"error": "No orders found"}), 404

    # For each order, add each image link
    for order in orders:
        for url in image_urls:
            deliver_note_image = DeliveryNoteImage(order_id=order.id, image_url=url)
            db.session.add(deliver_note_image)

    # Commit the changes to the database
    db.session.commit()

    return jsonify({"message": "Images uploaded and associated with orders successfully"}), 200