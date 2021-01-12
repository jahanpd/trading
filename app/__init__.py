# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

from flask import Flask
from config import Config
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
import pyrebase
import json

# initialize app
app = Flask(__name__)
app.config.from_object(Config)

# initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = '/login'
# initialize firebase authentication
firebase = pyrebase.initialize_app(app.config['FIREBASE_CONFIG'])
auth = firebase.auth()
db = firebase.database()

# Add bootstrap to app
Bootstrap(app)

# import blueprints
from .views.home import home
from .views.login import login_b
from .views.portfolio import portfolio
# register blueprints
app.register_blueprint(home)
app.register_blueprint(login_b)
app.register_blueprint(portfolio)

