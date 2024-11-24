import os
import logging
import re
import time
import paramiko
from flask import Blueprint, jsonify, request, render_template, abort
from functools import wraps

# Initialize the blueprint
router_management = Blueprint('router_management', __name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Logging setup
logging.basicConfig(
    filename='logs/router_management.log',
    level=logging.DEBUG,
    format=('%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - '
            'Line: %(lineno)d - %(message)s')
)

# Logging Decorator
def log_route(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Endpoint {request.path} called with method {request.method}")
        if request.method == "POST":
            sanitized_data = {k: ("***" if k == "password" else v) for k, v in request.json.items()}
            logging.debug(f"Request Data: {sanitized_data}")
        response = func(*args, **kwargs)
        logging.info(f"Response: {response.status_code}")
        return response
    return wrapper

# SSH Utilities
def execute_command_on_router(router_ip, username, password, command, retries=3, delay=2):
    """Execute a command on the router using SSH."""
    logging.info(f"Executing command on router {router_ip}: {command}")
    for attempt in range(retries):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(router_ip, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            ssh.close()
            return output, error
        except paramiko.SSHException as ssh_error:
            logging.error(f"SSH error on attempt {attempt + 1}: {ssh_error}")
            time.sleep(delay)
    logging.error(f"Failed to execute command after {retries} attempts on router {router_ip}")
    return None, "Failed after multiple attempts."

def fetch_dhcp_pool_range(router_ip, username, password):
    """Fetch the DHCP pool range from the router configuration."""
    command = "uci show dhcp"
    output, _ = execute_command_on_router(router_ip, username, password, command)
    if not output:
        return None, None

    pool_start_match = re.search(r"dhcp\.lan\.start='(\d+)'", output)
    pool_limit_match = re.search(r"dhcp\.lan\.limit='(\d+)'", output)
    if pool_start_match and pool_limit_match:
        pool_start = int(pool_start_match.group(1))
        pool_limit = int(pool_limit_match.group(1))
        base_ip = ".".join(router_ip.split('.')[:3])
        return f"{base_ip}.{pool_start}", f"{base_ip}.{pool_start + pool_limit - 1}"
    return None, None

def list_connected_devices(router_ip, username, password):
    """Fetch connected devices from the router."""
    command = "cat /tmp/dhcp.leases"
    output, error = execute_command_on_router(router_ip, username, password, command)
    if error:
        logging.error(f"Error fetching connected devices: {error}")
        return []

    devices = []
    for line in output.strip().split("\n"):
        parts = line.split()
        if len(parts) >= 4:
            lease_time, mac, ip, hostname = parts[:4]
            devices.append({
                "lease_time": int(lease_time),
                "mac_address": mac,
                "ip_address": ip,
                "hostname": hostname
            })
    logging.info(f"Found {len(devices)} connected devices.")
    return devices

def list_all_ips_with_occupancy(router_ip, username, password):
    """Generate a complete list of IPs (1-255) with occupancy status."""
    logging.info(f"Generating full IP list with occupancy status for router {router_ip}")
    pool_start, pool_end = fetch_dhcp_pool_range(router_ip, username, password)
    base_ip = ".".join(router_ip.split('.')[:3])

    # Generate all IPs in the range 1-255
    all_ips = [f"{base_ip}.{i}" for i in range(1, 256)]

    # Fetch connected devices
    connected_devices = list_connected_devices(router_ip, username, password)
    occupied_ips = {device["ip_address"]: device for device in connected_devices}

    # Build the response with full IP table
    ip_list = []
    for ip in all_ips:
        device_info = occupied_ips.get(ip, {})
        ip_list.append({
            "ip_address": ip,
            "in_dhcp_pool": pool_start <= ip <= pool_end if pool_start and pool_end else False,
            "occupied": ip in occupied_ips,
            "hostname": device_info.get("hostname", "Unknown"),
            "mac_address": device_info.get("mac_address", ""),
            "lease_time": device_info.get("lease_time", 0)
        })

    logging.info(f"Generated list of {len(ip_list)} IPs with occupancy status.")
    return ip_list

def change_device_ip(router_ip, username, password, mac, new_ip):
    """Change the static IP binding for a device on the router."""
    command = (
        f"uci add dhcp host; "
        f"uci set dhcp.@host[-1].mac='{mac}'; "
        f"uci set dhcp.@host[-1].ip='{new_ip}'; "
        f"uci commit dhcp; "
        f"/etc/init.d/dnsmasq restart"
    )
    _, error = execute_command_on_router(router_ip, username, password, command)
    return (True, "IP updated successfully.") if not error else (False, error)

# Routes
@router_management.route('/router_management', methods=['GET'])
def render_router_management_page():
    """Render the Router Management page."""
    return render_template('router_management.html')

@router_management.route('/devices', methods=['GET'])
@log_route
def get_devices():
    """Fetch a complete list of IPs with occupancy and device details."""
    try:
        router_ip = request.args.get('router_ip', '192.168.8.1')
        username = request.args.get('username', 'root')
        password = request.args.get('password', '123456')

        # Fetch the full IP list with occupancy status
        ip_list = list_all_ips_with_occupancy(router_ip, username, password)

        return jsonify(ip_list)
    except Exception as e:
        logging.error(f"Error fetching devices: {str(e)}")
        return jsonify({"error": "Failed to fetch devices", "details": str(e)}), 500

@router_management.route('/change_ip', methods=['POST'])
@log_route
def change_ip():
    """Change a device's IP address."""
    data = request.json
    if not data or 'mac' not in data or 'new_ip' not in data:
        abort(400, description="Invalid input: 'mac' and 'new_ip' are required fields.")
    try:
        router_ip = data.get('router_ip', '192.168.8.1')
        username = data.get('username', 'root')
        password = data.get('password', '123456')
        success, message = change_device_ip(router_ip, username, password, data['mac'], data['new_ip'])
        return jsonify({"success": success, "message": message})
    except Exception as e:
        logging.error(f"Error changing IP: {str(e)}")
        return jsonify({"error": "Failed to change IP", "details": str(e)}), 500
