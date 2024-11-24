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

# Logger setup
logger = logging.getLogger(__name__)

# Function to log user activity
def get_ip_status(ip_address):
    """Mock function to determine the status of the given IP."""
    # Logic to determine IP status, this can vary depending on how you track IP statuses
    # Here’s a basic example:
    mongo = current_app.extensions['pymongo']
    ip_data = mongo.db.ip_allocations.find_one({"ip_address": ip_address})
    if ip_data and ip_data.get("status") == "online":
        return "online"
    return "offline"

def log_activity(action, details):
    """Logs user activity into MongoDB."""
    mongo = current_app.extensions['pymongo']
    activity = {
        "user_id": current_user.get_id(),
        "username": current_user.username if current_user.is_authenticated else "system",
        "action": action,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    mongo.db.activities.insert_one(activity)
    current_app.logger.info(f"Activity logged: {activity}")

# Function to validate IP address
def validate_ip(ip):
    """Validates if the provided IP address is in a correct format."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

# Function to convert ObjectId to string
def convert_objectid(obj):
    """Converts ObjectId to string."""
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Error handling for validation issues
def handle_validation_error(message):
    logger.warning(f"Validation error: {message}")
    return jsonify(message=message), 400

# Error handling for database issues
def handle_database_error(message):
    logger.error(f"Database error: {message}")
    return jsonify(message="Database error", error=message), 500

# GL.iNet router settings
# Define your router's credentials and API endpoint
router_ip = "192.168.10.10"  # Replace with your router's IP
url = f"http://{router_ip}/rpc"
username = "root"  # Replace with your router's username
password = "153246#pota"  # Replace with your router's password


def get_encryption_parameters():
    response = requests.post(url, json={
        "jsonrpc": "2.0",
        "method": "challenge",
        "params": {"username": username},
        "id": 0
    })
    print("Encryption parameters response:", response.text)  # Print the raw response
    data = response.json().get('result', {})
    return data.get('alg'), data.get('salt'), data.get('nonce')


def generate_cipher_password(alg, salt, password):
    if alg == 1:
        return md5_crypt.using(salt=salt).hash(password)
    elif alg == 5:
        return sha256_crypt.using(salt=salt).hash(password)
    elif alg == 6:
        return sha512_crypt.using(salt=salt).hash(password)


def login():
    try:
        alg, salt, nonce = get_encryption_parameters()
        cipher_password = generate_cipher_password(alg, salt, password)
        hash_value = hashlib.md5(f"{username}:{cipher_password}:{nonce}".encode()).hexdigest()
        response = requests.post(url, json={
            "jsonrpc": "2.0",
            "method": "login",
            "params": {"username": username, "hash": hash_value},
            "id": 0
        })
        print("Login response:", response.text)  # Print the raw response for debugging
        return response.json()['result']['sid']
    except Exception as e:
        print("Login failed:", e)
        return None


def block_ip(ip_to_block):
    sid = login()
    if not sid:
        return {"error": "Login failed, no session ID returned."}

    response = requests.post(url, json={
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

    try:
        response_data = response.json()
        return response_data
    except ValueError:
        return {"error": "Failed to parse response from API."}

