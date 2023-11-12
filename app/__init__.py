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

    from datetime import datetime, timedelta

    def adjust_week(week_str, delta_weeks):
        year, week = map(int, week_str.split('-W'))
        start_of_week = datetime.fromisocalendar(year, week, 1)
        adjusted_date = start_of_week + timedelta(weeks=delta_weeks)
        adjusted_year, adjusted_week, _ = adjusted_date.isocalendar()
        adjusted_week_str = f"{adjusted_year}-W{adjusted_week:02d}"
        return adjusted_week_str

    app.register_blueprint(routes.bp)

    # Define and add the custom filter
    @app.template_filter('adjust_week')
    def adjust_week_filter(week_str, delta_weeks):
        return adjust_week(week_str, delta_weeks)
    return app
