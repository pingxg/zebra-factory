import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqldb://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@"
        f"{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}?charset=utf8mb4"
    )
    SQLALCHEMY_POOL_SIZE = 15
    SQLALCHEMY_POOL_TIMEOUT = 10
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
