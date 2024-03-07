import os
from flask import Flask
from .config import Config
from .extensions import db, login_manager, socketio
from .template_filters import register_template_filters
from dotenv import load_dotenv
from .blueprints.main import main_bp
from .blueprints.auth import auth_bp
from .blueprints.order import order_bp
# from .blueprints.weight import weight_bp
# from .blueprints.printing import printing_bp
from .blueprints.customer import customer_bp
from .blueprints.product import product_bp
# from .blueprints.user import user_bp



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
    load_dotenv()

    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    app.jinja_env.add_extension('jinja2.ext.do')

    login_manager.login_view = 'auth.login'


    # Custom JSON encoder
    from .utils.helper import CustomJSONEncoder
    app.json_encoder = CustomJSONEncoder


    @app.context_processor
    def inject_global_vars():
        return dict(completion_threshold=os.environ.get('COMPLETION_THRESHOLD', 0.9),
                    completion_threshold_upper=os.environ.get('COMPLETION_THRESHOLD_UPPER', 1.3))

    # Register blueprints
    from . import routes            

    app.register_blueprint(routes.bp, url_prefix='/')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(order_bp, url_prefix='/order')
    # app.register_blueprint(weight_bp, url_prefix='/weight')
    # app.register_blueprint(printing_bp, url_prefix='/printing')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(product_bp, url_prefix='/product')
    # app.register_blueprint(user_bp, url_prefix='/user')


    # Register custom template filters
    register_template_filters(app)

    return app

