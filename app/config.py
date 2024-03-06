import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configures database and session settings.
    # - SQLALCHEMY_DATABASE_URI: Connection string for database. Uses environment variables for credentials and host details.
    # - SQLALCHEMY_POOL_SIZE: Number of connections to pool in database connection pool. 
    # - SQLALCHEMY_POOL_TIMEOUT: Time to wait before releasing idle connections in pool.
    # - SQLALCHEMY_TRACK_MODIFICATIONS: Whether to track modifications on ORM models.
    # - REMEMBER_COOKIE_DURATION: Lifetime of remember me cookies.
    # - SECRET_KEY: Secret key for cryptographic functions like signing cookies.
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
        'admin': ['add_weight', 'print_labels', 'edit_order', 'upload_delivery_note', 'view'],
        'editor': ['add_weight', 'print_labels', 'view'],
        'driver': ['upload_delivery_note', 'view'],
        'viewer': ['view'],
    }