# utils.py

from flask import current_app, jsonify
from flask_login import current_user
from datetime import datetime
import ipaddress
from bson import ObjectId
import logging
import requests
import hashlib
from passlib.hash import md5_crypt, sha256_crypt, sha512_crypt
from functools import wraps

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - Line: %(lineno)d - %(message)s'
)

# Centralized router credentials
ROUTER_CONFIG = {
    "router_ip": "192.168.8.1",
    "url": f"http://192.168.8.1/rpc",
    "username": "root",
    "password": "123456"
}

# Function to log user activity
def log_activity(action, details):
    """Logs user activity into MongoDB."""
    try:
        mongo = current_app.extensions['pymongo']
        activity = {
            "user_id": current_user.get_id(),
            "username": current_user.username if current_user.is_authenticated else "system",
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mongo.db.activities.insert_one(activity)
        logger.info(f"Activity logged: {activity}")
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")

# General utility functions
def validate_ip(ip):
    """Validates if the provided IP address is in a correct format."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def convert_objectid(obj):
    """Converts ObjectId to string."""
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Error handling functions
def handle_validation_error(message):
    """Handles validation errors."""
    logger.warning(f"Validation error: {message}")
    return jsonify(message=message), 400

def handle_database_error(message):
    """Handles database errors."""
    logger.error(f"Database error: {message}")
    return jsonify(message="Database error", error=message), 500

# Logging decorator
def log_route(func):
    """Decorator for logging API routes."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Endpoint {current_app.name}{func.__name__} called.")
        try:
            response = func(*args, **kwargs)
            
            # Handle string responses or objects without a `status_code` attribute
            if isinstance(response, str):
                logger.info(f"Response: {response}")
            elif hasattr(response, 'status_code'):
                logger.info(f"Response: {response.status_code}")
            else:
                logger.warning("Response has no status_code and is not a string.")

            return response
        except Exception as e:
            logger.error(f"Error in route {func.__name__}: {e}")
            raise
    return wrapper

# GL.iNet router-related functions
def get_encryption_parameters():
    """Fetch encryption parameters for login."""
    try:
        response = requests.post(ROUTER_CONFIG["url"], json={
            "jsonrpc": "2.0",
            "method": "challenge",
            "params": {"username": ROUTER_CONFIG["username"]},
            "id": 0
        })
        response.raise_for_status()
        data = response.json().get('result', {})
        return data.get('alg'), data.get('salt'), data.get('nonce')
    except Exception as e:
        logger.error(f"Failed to get encryption parameters: {e}")
        raise

def generate_cipher_password(alg, salt, password):
    """Generate a cipher password based on the algorithm and salt."""
    if alg == 1:
        return md5_crypt.using(salt=salt).hash(password)
    elif alg == 5:
        return sha256_crypt.using(salt=salt).hash(password)
    elif alg == 6:
        return sha512_crypt.using(salt=salt).hash(password)
    else:
        raise ValueError("Unsupported encryption algorithm.")

def login():
    """Login to the router and fetch session ID."""
    try:
        alg, salt, nonce = get_encryption_parameters()
        cipher_password = generate_cipher_password(alg, salt, ROUTER_CONFIG["password"])
        hash_value = hashlib.md5(
            f"{ROUTER_CONFIG['username']}:{cipher_password}:{nonce}".encode()
        ).hexdigest()
        response = requests.post(ROUTER_CONFIG["url"], json={
            "jsonrpc": "2.0",
            "method": "login",
            "params": {"username": ROUTER_CONFIG["username"], "hash": hash_value},
            "id": 0
        })
        response.raise_for_status()
        return response.json()['result']['sid']
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise

def block_ip(ip_to_block):
    """Block an IP address via the router's firewall."""
    try:
        sid = login()
        response = requests.post(ROUTER_CONFIG["url"], json={
            "jsonrpc": "2.0",
            "method": "call",
            "params": [
                sid,
                "firewall",  # Confirm this module name
                "add_rule",  # Confirm this method for adding a rule
                {"ip": ip_to_block, "action": "block"}
            ],
            "id": 0
        })
        response.raise_for_status()
        logger.info(f"Blocked IP {ip_to_block}: {response.json()}")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to block IP {ip_to_block}: {e}")
        raise
