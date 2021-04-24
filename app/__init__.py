

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://rhyrskgomkidbu:13045206abc03d99ce516cb0120f1e124f1a2919ccd641b8ae142c34aacbe3f7@ec2-54-204-96-190.compute-1.amazonaws.com:5432/d3a74mcg9rq95d'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.debug = True
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
socketio=SocketIO(app)

from . import routes  # noqa
