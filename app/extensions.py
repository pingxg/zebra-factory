from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_toastr import Toastr

# Initialize Flask extensions here
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
toastr = Toastr()