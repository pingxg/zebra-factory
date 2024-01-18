from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_name):
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
    app.config.from_object(config_name)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    socketio.init_app(app, cors_allowed_origins="*")
    
    from . import routes

    from datetime import datetime, timedelta

    def adjust_week(week_str, delta_weeks):
        year, week = map(int, week_str.split('-W'))
        start_of_week = datetime.fromisocalendar(year, week, 1)
        adjusted_date = start_of_week + timedelta(weeks=delta_weeks)
        adjusted_year, adjusted_week, _ = adjusted_date.isocalendar()
        adjusted_week_str = f"{adjusted_year}-W{adjusted_week:02d}"
        return adjusted_week_str

    def add_days(date_str, days, date_format="%Y-%m-%d"):
        # Convert the string to a datetime object
        dt = datetime.strptime(date_str, date_format)
        # Add the specified number of days
        new_date = dt + timedelta(days=days)
        # Convert back to string if needed, or return the datetime object
        return new_date.strftime(date_format)

    app.register_blueprint(routes.bp)

    # Define and add the custom filter
    @app.template_filter('adjust_week')
    def adjust_week_filter(week_str, delta_weeks):
        return adjust_week(week_str, delta_weeks)
    # Define and add the custom filter
    @app.template_filter('add_days')
    def add_days_filter(date_str, days):
        return add_days(date_str, days)
        
    return app
