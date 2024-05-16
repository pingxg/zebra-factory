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

        s3 = boto3.client(
            's3',
            config=Config(signature_version='s3v4'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION')
        )
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


@deliverynote_bp.route('/get-presigned-urls/<int:order_id>', methods=['GET'])
@roles_required('admin', 'driver')
def get_presigned_urls(order_id):
    # Query to get all image URLs for the given order ID, sorted by update rate (assumed to be the 'updated_at' field)
    images = DeliveryNoteImage.query.filter_by(order_id=order_id).order_by(DeliveryNoteImage.updated_at).all()

    if not images:
        return jsonify({"error": "No images found"}), 404

    s3 = boto3.client(
        's3',
        config=Config(signature_version='s3v4'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION')
    )
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    presigned_urls = []

    for image in images:
        presigned_url = s3.generate_presigned_url('get_object',
                                                  Params={'Bucket': bucket_name, 'Key': image.image_url},
                                                  ExpiresIn=3600)  # URL expiration time in seconds
        presigned_urls.append({
            "image_id": image.id,
            "presigned_url": presigned_url
        })

    return jsonify(presigned_urls), 200



@deliverynote_bp.route('/delete-image', methods=['DELETE'])
@roles_required('admin', 'driver')
def delete_image():
    data = request.get_json()
    image_id = data.get('image_id')
    presigned_url = data.get('presigned_url')

    if not presigned_url or not image_id:
        return jsonify({"error": "Presigned URL and image ID are required"}), 400

    # Extract the key from the presigned URL
    import urllib
    from urllib.parse import urlparse

    url_parts = urlparse(presigned_url)
    key = url_parts.path.lstrip('/').strip()
    key = urllib.parse.unquote(key)

    s3 = boto3.client(
        's3',
        config=Config(signature_version='s3v4'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION')
    )
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')

    try:
        # Get the image record by image_id to retrieve the image_url
        image_record = DeliveryNoteImage.query.get(image_id)
        if not image_record:
            return jsonify({"error": "Image record not found in the database"}), 404
        
        image_url = image_record.image_url

        # Attempt to delete the image file from S3
        response = s3.delete_object(Bucket=bucket_name, Key=key)
        
        # Check if the image was successfully deleted from S3
        if response['ResponseMetadata']['HTTPStatusCode'] == 204:
            # Find all image records with the same image URL
            images = DeliveryNoteImage.query.filter_by(image_url=image_url).all()

            # Delete all found image records from the database
            for image in images:
                db.session.delete(image)
            db.session.commit()
            
            flash("All related image records and corresponding file deleted successfully!", 'success')
            return jsonify({"message": "All related image records and corresponding file deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete image from S3"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500