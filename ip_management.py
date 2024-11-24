from flask import Blueprint, jsonify, request, current_app, render_template, session, redirect, url_for
from datetime import datetime
import logging
import nmap
import ipaddress
from utils import (
    log_activity,
    validate_ip,
    convert_objectid,
    handle_validation_error,
    handle_database_error,
    block_ip,
)
from mac_parser import load_manuf_file, get_manufacturer

# Initialize the blueprint
ip_management = Blueprint('ip_management', __name__)

# Logger setup
logger = logging.getLogger(__name__)

# Load manufacturer data at the start of the application
manuf_file_path = 'data/manuf.txt'  # Ensure this path is correct
manuf_dict = load_manuf_file(manuf_file_path)  # Load manufacturers from the OUI database


# Network Scanning and Device Management
def scan_network_and_update_db(ip_range):
    """Scan the network and update the IP status in the database."""
    scanner = nmap.PortScanner()
    scanner.scan(hosts=ip_range, arguments='-sn')  # -sn for host discovery (ping scan)
    scanned_ips = set()
    mongo = current_app.extensions['pymongo']

    # Scan devices and update their status
    for host in scanner.all_hosts():
        if 'ipv4' in scanner[host]['addresses']:
            ip_address = scanner[host]['addresses']['ipv4']
            scanned_ips.add(ip_address)

            mac_address = scanner[host]['addresses'].get('mac', 'N/A')
            manufacturer = get_manufacturer(mac_address, manuf_dict)

            device = {
                'ip_address': ip_address,
                'status': 'online',
                'mac': mac_address,
                'device_name': manufacturer,
                'last_seen': datetime.utcnow().isoformat() + "Z",
            }

            # Upsert the device into MongoDB
            mongo.db.ip_allocations.update_one({"ip_address": ip_address}, {"$set": device}, upsert=True)

    # Mark unscanned devices as offline
    mongo.db.ip_allocations.update_many(
        {"ip_address": {"$nin": list(scanned_ips)}},
        {"$set": {"status": "offline"}}
    )

    # Retrieve all devices (online and offline)
    all_devices = list(mongo.db.ip_allocations.find())
    for device in all_devices:
        if '_id' in device:
            device['_id'] = str(device['_id'])

    return all_devices


@ip_management.route('/scan_network', methods=['GET'])
def scan_network_route():
    """Route to scan the network."""
    try:
        router_ip = session.get('router_ip')
        if not router_ip:
            return redirect(url_for('set_router_ip'))

        ip_range = request.args.get("ip_range", f"{router_ip}/24")
        devices = scan_network_and_update_db(ip_range)
        return jsonify(devices=devices), 200
    except Exception as e:
        logger.error(f"Error scanning network: {e}")
        return handle_database_error(f"Error scanning network: {e}")


@ip_management.route('/get_last_scan', methods=['GET'])
def get_last_scan():
    """Route to fetch the last scan data."""
    try:
        mongo = current_app.extensions['pymongo']
        last_scan = mongo.db.ip_allocations.find().sort("last_seen", -1)
        devices = list(last_scan)
        for device in devices:
            device['_id'] = convert_objectid(device.get('_id'))
        return jsonify(devices=devices)
    except Exception as e:
        return handle_database_error(f"Error retrieving last scan: {str(e)}")


@ip_management.route('/scan_device', methods=['GET'])
def scan_device_route():
    """Route to scan a single device."""
    try:
        ip_address = request.args.get('ip_address')
        if not validate_ip(ip_address):
            return handle_validation_error("Invalid IP address")

        scanner = nmap.PortScanner()
        scanner.scan(hosts=ip_address, arguments='-sn')

        if ip_address in scanner.all_hosts():
            mac_address = scanner[ip_address]['addresses'].get('mac', 'N/A')
            manufacturer = get_manufacturer(mac_address, manuf_dict)
            device = {
                'ip_address': ip_address,
                'status': 'online',
                'mac': mac_address,
                'device_name': manufacturer,
                'last_seen': datetime.utcnow().isoformat() + "Z",
            }
        else:
            device = {
                'ip_address': ip_address,
                'status': 'offline',
                'mac': 'N/A',
                'device_name': 'Unknown device',
                'last_seen': datetime.utcnow().isoformat() + "Z",
            }

        mongo = current_app.extensions['pymongo']
        mongo.db.ip_allocations.update_one({"ip_address": ip_address}, {"$set": device}, upsert=True)
        log_activity("Device Scan", f"Scanned device with IP {ip_address}")

        return jsonify(device=device), 200
    except Exception as e:
        logger.error(f"Error scanning device: {str(e)}")
        return handle_database_error(f"Error scanning device: {str(e)}")


# IP Allocation and Management
@ip_management.route('/allocate_ip', methods=['POST'])
def allocate_ip():
    """Route to allocate IP to a device."""
    try:
        data = request.json
        ip_address = data.get('ip_address')
        device_name = data.get('device_name')

        if not validate_ip(ip_address):
            return handle_validation_error("Invalid IP address")

        mongo = current_app.extensions['pymongo']
        mongo.db.ip_allocations.update_one(
            {"ip_address": ip_address},
            {
                "$set": {
                    "ip_address": ip_address,
                    "allocated": True,
                    "reserved": False,
                    "device_name": device_name,
                    "allocated_time": datetime.utcnow().isoformat() + "Z",
                }
            },
            upsert=True
        )
        log_activity("IP Allocation", f"Allocated IP {ip_address} to {device_name}")
        return jsonify(message=f"IP {ip_address} allocated successfully to {device_name}"), 200
    except Exception as e:
        logger.error(f"Error allocating IP: {str(e)}")
        return handle_database_error(f"Error allocating IP: {str(e)}")


@ip_management.route('/reserve_ip', methods=['POST'])
def reserve_ip():
    """Route to reserve an IP address."""
    try:
        data = request.json
        ip_address = data.get('ip_address')

        if not validate_ip(ip_address):
            return handle_validation_error("Invalid IP address")

        mongo = current_app.extensions['pymongo']
        mongo.db.ip_allocations.update_one(
            {"ip_address": ip_address},
            {
                "$set": {
                    "ip_address": ip_address,
                    "allocated": False,
                    "reserved": True,
                    "reserved_time": datetime.utcnow().isoformat() + "Z",
                }
            },
            upsert=True
        )
        log_activity("IP Reservation", f"Reserved IP {ip_address}")
        return jsonify(message=f"IP {ip_address} reserved successfully"), 200
    except Exception as e:
        logger.error(f"Error reserving IP: {str(e)}")
        return handle_database_error(f"Error reserving IP: {str(e)}")


@ip_management.route('/release_ip', methods=['POST'])
def release_ip():
    """Route to release an IP address."""
    try:
        data = request.json
        ip_address = data.get('ip_address')

        if not validate_ip(ip_address):
            return handle_validation_error("Invalid IP address")

        mongo = current_app.extensions['pymongo']
        result = mongo.db.ip_allocations.delete_one({"ip_address": ip_address})

        if result.deleted_count == 0:
            return jsonify(message=f"No IP found with address {ip_address}"), 404

        log_activity("IP Release", f"Released IP {ip_address}")
        return jsonify(message=f"IP {ip_address} released successfully"), 200
    except Exception as e:
        logger.error(f"Error releasing IP: {str(e)}")
        return handle_database_error(f"Error releasing IP: {str(e)}")


@ip_management.route('/block_ip', methods=['POST'])
def block_ip_route():
    """Route to block an IP address."""
    try:
        data = request.get_json()
        ip_address = data.get("ip_address")
        if not ip_address:
            return jsonify({"error": "IP address is required"}), 400

        result = block_ip(ip_address)
        if 'error' in result:
            return jsonify({"error": result['error']}), 500
        return jsonify({"message": f"IP {ip_address} blocked successfully"}), 200
    except Exception as e:
        logger.error(f"Error blocking IP: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ip_management.route('/manage_ip', methods=['GET'])
def render_manage_ip_page():
    """Render the Manage IP page."""
    return render_template('manage_ip.html')
