from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://hvgpayytgzdriz:8866ed90209b425b1564220054fcb02a4294dd90e9021bf4fd74f11d496a6783@ec2-54-235-192-146.compute-1.amazonaws.com:5432/d18fcqbriqdia7'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.debug=True
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from ecotravel import routes
