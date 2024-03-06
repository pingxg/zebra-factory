from flask import Flask
from .config import Config
from .extensions import db, login_manager, socketio
from .template_filters import register_template_filters
from dotenv import load_dotenv
from .blueprints.auth import auth_bp
# from .blueprints.orders import orders_bp
# from .blueprints.main import main_bp


def create_app() -> Flask:
    """Creates the Flask application instance.
    
    Initializes and configures the Flask app, SQLAlchemy, Flask-Login, 
    Flask-SocketIO, loads environment variables, registers blueprints and template
    filters.
    
    Args:
        config_name: The configuration to use for the app.
    
    Returns:
        The configured Flask app instance.
    """
    load_dotenv()  # Load environment variables from .env
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    app.jinja_env.add_extension('jinja2.ext.do')

    login_manager.login_view = 'auth.login'

    # Register blueprints
    from . import routes

    # Custom JSON encoder
    from .utils.helper import CustomJSONEncoder
    app.json_encoder = CustomJSONEncoder

    app.register_blueprint(routes.bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    # app.register_blueprint(orders_bp, url_prefix='/orders')


    # Register custom template filters
    register_template_filters(app)

    return app
