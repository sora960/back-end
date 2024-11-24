from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', '6969696')  # Ensure secret key is secure

# Enable CORS
CORS(app)

# MongoDB configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/ip_management_system")
mongo = PyMongo(app)

# Ensure MongoDB is added to extensions (important for current_app usage)
app.extensions['pymongo'] = mongo

# Flask-Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure MongoDB connection works
try:
    mongo.db.list_collection_names()
    print("MongoDB connected successfully.")
except Exception as e:
    logger.error(f"MongoDB connection error: {e}")

# User loader for Flask-Login
from auth import User  # Import the User class from auth.py
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Register Blueprints
from ip_management import ip_management
app.register_blueprint(ip_management)

from dashboard import dashboard as dashboard_bp
app.register_blueprint(dashboard_bp)

from speed_test import speedtest_bp
app.register_blueprint(speedtest_bp)

from report import report
app.register_blueprint(report)

from data_usage import data_usage
app.register_blueprint(data_usage)

from auth import auth
app.register_blueprint(auth)

from general import general
app.register_blueprint(general)

from ip_setup import ip_setup
app.register_blueprint(ip_setup)

from router_management import router_management
app.register_blueprint(router_management)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
