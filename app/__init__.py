from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_name):
    load_dotenv()  # Load environment variables from .env

    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_name)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    socketio.init_app(app, cors_allowed_origins="*")
    
    from . import routes
    app.register_blueprint(routes.bp)

    return app
