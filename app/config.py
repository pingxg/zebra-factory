import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqldb://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@"
        f"{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}?charset=utf8mb4"
    )
    SQLALCHEMY_POOL_SIZE = 15
    SQLALCHEMY_POOL_TIMEOUT = 10
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    SECRET_KEY = os.environ.get('SECRET_KEY')
    ROLE_PERMISSIONS = {
        'admin': ['edit_order', 'edit_weight', 'print_label', 'upload_delivery_note', 'download_delivery_note', 'edit_user', 'edit_label', 'edit_product', 'edit_customer'],
        'cutter': ['edit_weight', 'print_label', 'download_delivery_note'],
        'driver': ['upload_delivery_note', 'download_delivery_note'],
    }
    
    TOASTR_TIMEOUT  = 2000
    TOASTR_EXTENDED_TIMEOUT = 1000
    TOASTR_POSITION_CLASS = 'toast-top-center'
    TOASTR_NEWS_ON_TOP = 'true'
    TOASTR_PREVENT_DUPLICATES = 'true'
    TOASTR_CLOSE_BUTTON = 'false'
    TOASTR_CLOSE_DURATION = 100