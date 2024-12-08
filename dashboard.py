from flask import Blueprint, jsonify, current_app, render_template, request
import logging
import requests
from datetime import datetime

# Initialize the blueprint
dashboard = Blueprint('dashboard', __name__)

# Logger setup
logger = logging.getLogger(__name__)

@dashboard.route('/dashboard_data', methods=['GET'])
def get_dashboard_data():
    try:
        # Ensure PyMongo is initialized
        if 'pymongo' not in current_app.extensions:
            raise RuntimeError("PyMongo is not properly initialized.")

        mongo = current_app.extensions['pymongo']

        # Quick Summary: Fetch device information from the `devices` collection
        total_ips = 254  # Example for a /24 subnet
        allocated_ips = mongo.db.devices.count_documents({})  # Count all devices in the collection
        available_ips = total_ips - allocated_ips

        # Debug Quick Summary
        logger.debug(f"Quick Summary: Total: {total_ips}, Allocated: {allocated_ips}, Available: {available_ips}")

        # Fetch speed test history (last 10 results)
        speed_tests = mongo.db.speed_tests.find().sort("timestamp", -1).limit(10)
        speed_test_history = [
            {
                "download_speed": test.get('download_speed', 0),
                "upload_speed": test.get('upload_speed', 0),
                "ping": test.get('ping', 0),
                "timestamp": test.get('timestamp', "No data")
            }
            for test in speed_tests
        ]
        # Debug Speed Test History
        logger.debug(f"Speed Test History: {speed_test_history}")

        # Fetch data usage history (last 7 days)
        data_usage = mongo.db.data_usage.find().sort("timestamp", -1).limit(7)
        data_usage_history = [
            {
                "day": usage.get('day', "N/A"),
                "download": usage.get('download', 0),
                "upload": usage.get('upload', 0)
            }
            for usage in data_usage
        ]
        # Debug Data Usage History
        logger.debug(f"Data Usage History: {data_usage_history}")

        # Fetch recent activities (last 5 entries) from the `activities` collection
        recent_activities = mongo.db.activities.find().sort("timestamp", -1).limit(5)
        activity_log = []

        for activity in recent_activities:
            action = activity.get('action', "No activity")
            details = activity.get('details', {})
            timestamp = activity.get('timestamp', "N/A")

            # Format details based on action
            if action == "IP Assignment":
                details = f"Assigned IP {details.get('ip_address', 'N/A')} to device with MAC {details.get('mac_address', 'N/A')}."
            elif action == "Device Block":
                details = f"Blocked MAC {details.get('mac_address', 'N/A')}."
            elif action == "Device Unblock":
                details = f"Unblocked MAC {details.get('mac_address', 'N/A')}."
            elif action == "Data Usage Tracking":
                details = f"Tracked data usage: Download={details.get('download', 0)} MB, Upload={details.get('upload', 0)} MB."
            elif action == "Speed Test":
                details = f"Speed test results: Download={details.get('download_speed', 0)} Mbps, Upload={details.get('upload_speed', 0)} Mbps, Ping={details.get('ping', 0)} ms."
            else:
                details = "No details available"

            # Format timestamp into a readable format
            formatted_timestamp = datetime.fromisoformat(timestamp.replace("Z", "")).strftime("%I:%M %p %B %d, %Y") if isinstance(timestamp, str) else "Unknown Time"

            activity_log.append({
                "action": action,
                "details": details,
                "timestamp": formatted_timestamp
            })

        # Debug Recent Activity
        logger.debug(f"Recent Activity: {activity_log}")

        # Fetch public IP and ISP dynamically
        public_ip = "Unavailable"
        network_provider = "Unknown ISP"
        try:
            public_ip_response = requests.get('https://api64.ipify.org?format=json', timeout=5)
            print("Public IP Response:", public_ip_response.json())  # Debugging print
            public_ip = public_ip_response.json().get('ip', 'Unavailable')

            ipinfo_response = requests.get(f'https://ipinfo.io/{public_ip}?token=97d409f854b926', timeout=5)
            print("IP Info Response:", ipinfo_response.json())  # Debugging print
            ipinfo_data = ipinfo_response.json()
            network_provider = ipinfo_data.get('org', 'Unknown ISP')
        except requests.exceptions.RequestException as req_e:
            logger.error(f"Failed to fetch IP/ISP details: {req_e}")

        # Debug Public IP and Network Provider
        logger.debug(f"Public IP: {public_ip}, Network Provider: {network_provider}")

        # Structure data for the frontend
        dashboard_data = {
            "quick_summary": {
                "total_ips": total_ips,
                "allocated_ips": allocated_ips,
                "available_ips": available_ips,
            },
            "speed_test_history": speed_test_history,
            "data_usage_history": data_usage_history,
            "recent_activity": activity_log,
            "your_ip": request.remote_addr,
            "network_info": {  # Wrap the IP and ISP data in a network_info object
            "yourIp": request.remote_addr,
            "publicIp": public_ip,
            "networkProvider": network_provider
             },
            "is_empty": not any([speed_test_history, data_usage_history, activity_log])
        }

        return jsonify(dashboard_data)  # Return JSON response

    except RuntimeError as re:
        logger.error(f"Runtime error: {str(re)}")
        return jsonify(message="Runtime error in dashboard", error=str(re)), 500
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify(message="Error fetching dashboard data", error=str(e)), 500

@dashboard.route('/dashboard', methods=['GET'])
def render_dashboard():
    try:
        # Render the dashboard HTML template
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard page: {e}")
        return jsonify({"error": "Failed to render dashboard"}), 500