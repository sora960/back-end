from flask import Blueprint, jsonify, request, render_template
import paramiko
import logging
import time
from functools import wraps
from utils import log_activity  # Centralized logging

# Initialize the blueprint
blocking_management = Blueprint('blocking_management', __name__)

# Router Configuration
ROUTER_IP = "192.168.8.1"
ROUTER_USERNAME = "root"
ROUTER_PASSWORD = "123456"

# Set of blocked devices
blocked_devices = set()

# Logging setup
logging.basicConfig(
    filename='logs/blocking_management.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Logging Decorator
def log_route(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Endpoint {request.path} called with method {request.method}")
        response = func(*args, **kwargs)
        logging.info(f"Response: {response.status_code}")
        return response
    return wrapper

# Utility Function: Execute SSH command on the router with retry mechanism
def execute_command_on_router(command, retries=3, delay=2):
    for attempt in range(retries):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ROUTER_IP, username=ROUTER_USERNAME, password=ROUTER_PASSWORD)
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            ssh.close()
            logging.debug(f"Command: {command}\nOutput: {output}\nError: {error}")
            return output, error
        except Exception as e:
            logging.error(f"SSH Command Error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None, str(e)

# Block a device by MAC address
def block_device(mac):
    logging.info(f"Attempting to block MAC: {mac}")
    command = f"uci add_list wireless.@wifi-iface[0].maclist='{mac}'; uci set wireless.@wifi-iface[0].macfilter='deny'; uci commit wireless; wifi"
    output, error = execute_command_on_router(command)
    if not error:
        blocked_devices.add(mac)
        logging.info(f"Device {mac} blocked successfully.")
        log_activity("Device Block", {"mac_address": mac})
        return True, "Device blocked successfully."
    logging.error(f"Error blocking device {mac}: {error}")
    log_activity("Device Block Error", {"mac_address": mac, "error": error})
    return False, f"Error blocking device: {error}"

# Unblock a device by MAC address
def unblock_device(mac):
    logging.info(f"Attempting to unblock MAC: {mac}")
    command = f"uci del_list wireless.@wifi-iface[0].maclist='{mac}'; uci commit wireless; wifi"
    output, error = execute_command_on_router(command)
    if not error:
        blocked_devices.discard(mac)
        logging.info(f"Device {mac} unblocked successfully.")
        log_activity("Device Unblock", {"mac_address": mac})
        return True, "Device unblocked successfully."
    logging.error(f"Error unblocking device {mac}: {error}")
    log_activity("Device Unblock Error", {"mac_address": mac, "error": error})
    return False, f"Error unblocking device: {error}"

# Get list of connected devices
def get_connected_devices():
    logging.info("Fetching connected devices...")
    command = "cat /tmp/dhcp.leases"
    output, error = execute_command_on_router(command)
    if error or not output:
        logging.error(f"Error fetching connected devices: {error}")
        return []
    devices = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            lease_time, mac, ip, hostname = parts[:4]
            devices.append({'mac_address': mac, 'ip_address': ip, 'hostname': hostname})
    logging.info(f"Found {len(devices)} connected devices.")
    return devices

# Routes
@blocking_management.route('/connected_devices', methods=['GET'])
@log_route
def connected_devices_route():
    devices = get_connected_devices()
    return jsonify(devices)

@blocking_management.route('/blocked_devices', methods=['GET'])
@log_route
def blocked_devices_route():
    return jsonify(list(blocked_devices))

@blocking_management.route('/block_device', methods=['POST'])
@log_route
def block_device_route():
    data = request.json
    mac = data.get('mac')
    if not mac:
        return jsonify({"success": False, "message": "MAC address is required."}), 400
    success, message = block_device(mac)
    return jsonify({"success": success, "message": message})

@blocking_management.route('/unblock_device', methods=['POST'])
@log_route
def unblock_device_route():
    data = request.json
    mac = data.get('mac')
    if not mac:
        return jsonify({"success": False, "message": "MAC address is required."}), 400
    success, message = unblock_device(mac)
    return jsonify({"success": success, "message": message})

@blocking_management.route('/')
def render_blocking_page():
    return render_template('blocking_management.html')
