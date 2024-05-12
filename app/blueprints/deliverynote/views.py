import os
import boto3
from flask import request, send_file, abort, jsonify
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

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

@deliverynote_bp.route('/upload_url', methods=['GET', 'POST'])
def upload_url():
    object_name = request.args.get('filename')
    content_type = request.args.get('content_type', 'application/octet-stream')

    # # Validate the file type
    # if not allowed_file(object_name):
    #     return jsonify({"error": "File type not allowed"}), 400

    # Generate a pre-signed URL for uploading
    try:
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': os.getenv('AWS_S3_BUCKET_NAME'),
                'Key': "object_name.pdf",
                'ContentType': content_type,
                # 'ACL': 'public-read'  # Modify or remove based on your security policies
            },
            ExpiresIn=3600  # URL expiration time
        )
        print(presigned_url)
        return jsonify({'url': presigned_url})
    except Exception as e:
        print(e)
        abort(500, description=str(e))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}  # Add or remove file types as needed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS