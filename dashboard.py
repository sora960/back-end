from flask import Blueprint, jsonify, current_app, render_template, request
from datetime import datetime
import logging
import requests

# Initialize the blueprint
dashboard = Blueprint('dashboard', __name__)

# Logger setup
logger = logging.getLogger(__name__)

@dashboard.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    try:
        # Check if pymongo is registered and accessible
        if 'pymongo' not in current_app.extensions:
            raise RuntimeError("PyMongo is not properly initialized.")

        mongo = current_app.extensions['pymongo']

        # Fetch data for the quick summary (total, allocated, available IPs)
        total_ips = mongo.db.ip_allocations.count_documents({})
        allocated_ips = mongo.db.ip_allocations.count_documents({"allocated": True})
        available_ips = total_ips - allocated_ips

        # Fetch IP status for the pie chart
        ip_status = {
            "total_ip": total_ips,
            "allocated_ip": allocated_ips,
            "available_ip": available_ips
        }

        # Fetch speed test history (last 10 results)
        speed_tests = mongo.db.speed_tests.find().sort("timestamp", -1).limit(10)
        speed_test_history = [
            {
                "download_speed": test.get('download_speed'),
                "upload_speed": test.get('upload_speed'),
                "ping": test.get('ping'),
                "timestamp": test.get('timestamp')  # Ensure timestamp consistency
            }
            for test in speed_tests
        ]

        # Fetch data usage history (for the past week)
        data_usage = mongo.db.data_usage.find().sort("timestamp", -1).limit(7)
        data_usage_history = [
            {
                "day": usage.get('day'),
                "download": usage.get('download'),
                "upload": usage.get('upload')
            }
            for usage in data_usage
        ]

        # Fetch recent activities (last 5 activities)
        recent_activities = mongo.db.activities.find().sort("timestamp", -1).limit(5)
        activity_log = [
            {
                "action": activity.get('action'),
                "details": activity.get('details'),
                "timestamp": activity.get('timestamp')
            }
            for activity in recent_activities
        ]

        # Structure the response for the dashboard
        dashboard_data = {
            "quick_summary": {
                "total_ips": total_ips,
                "allocated_ips": allocated_ips,
                "available_ips": available_ips,
            },
            "ip_status": ip_status,
            "speed_test_history": speed_test_history,
            "data_usage_history": data_usage_history,
            "recent_activity": activity_log,
            "your_ip": request.remote_addr,  # Dynamically fetch user's local IP
            "network_provider": "PLDT HOME FIBR"  # Example static data for the network provider
        }

        # Render the dashboard page, pass the data to the frontend
        return render_template('dashboard.html', dashboard_data=dashboard_data)

    except RuntimeError as re:
        logger.error(f"Runtime error: {str(re)}")
        return jsonify(message="Runtime error in dashboard", error=str(re)), 500
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify(message="Error fetching dashboard data", error=str(e)), 500


@dashboard.route('/api/dashboard_data', methods=['GET'])
def api_get_dashboard_data():
    try:
        # Check if pymongo is registered and accessible
        if 'pymongo' not in current_app.extensions:
            raise RuntimeError("PyMongo is not properly initialized.")

        mongo = current_app.extensions['pymongo']

        # Fetch data for the quick summary
        total_ips = mongo.db.ip_allocations.count_documents({})
        allocated_ips = mongo.db.ip_allocations.count_documents({"allocated": True})
        available_ips = total_ips - allocated_ips

        # Fetch IP status for the pie chart
        ip_status = {
            "total_ip": total_ips,
            "allocated_ip": allocated_ips,
            "available_ip": available_ips
        }

        # Fetch speed test history (last 10 results)
        speed_tests = mongo.db.speed_tests.find().sort("timestamp", -1).limit(10)
        speed_test_history = [
            {
                "download_speed": test.get('download_speed'),
                "upload_speed": test.get('upload_speed'),
                "ping": test.get('ping'),
                "timestamp": test.get('timestamp')
            }
            for test in speed_tests
        ]

        # Fetch data usage history (for the past week)
        data_usage = mongo.db.data_usage.find().sort("timestamp", -1).limit(7)
        data_usage_history = [
            {
                "day": usage.get('day'),
                "download": usage.get('download'),
                "upload": usage.get('upload')
            }
            for usage in data_usage
        ]

        # Fetch recent activities (last 5 activities)
        recent_activities = mongo.db.activities.find().sort("timestamp", -1).limit(5)
        activity_log = [
            {
                "action": activity.get('action'),
                "details": activity.get('details'),
                "timestamp": activity.get('timestamp')
            }
            for activity in recent_activities
        ]

        # Get the local IP of the user
        local_ip = request.remote_addr

        # Fetch the public IP and ISP details using ipinfo.io
        public_ip = "Unavailable"
        network_provider = "Unknown ISP"
        try:
            public_ip_response = requests.get('https://api64.ipify.org?format=json', timeout=5)
            public_ip = public_ip_response.json().get('ip', 'Unavailable')

            ipinfo_response = requests.get(f'https://ipinfo.io/{public_ip}?token=97d409f854b926', timeout=5)
            ipinfo_data = ipinfo_response.json()
            network_provider = ipinfo_data.get('org', 'Unknown ISP')
        except requests.exceptions.RequestException as req_e:
            logger.error(f"Failed to fetch IP info: {str(req_e)}")

        dashboard_data = {
            "quick_summary": {
                "total_ips": total_ips,
                "allocated_ips": allocated_ips,
                "available_ips": available_ips,
            },
            "ip_status": ip_status,
            "speed_test_history": speed_test_history,
            "data_usage_history": data_usage_history,
            "recent_activity": activity_log,
            "your_ip": local_ip,
            "network_provider": network_provider
        }

        return jsonify(dashboard_data)

    except RuntimeError as re:
        logger.error(f"Runtime error: {str(re)}")
        return jsonify(message="Runtime error in dashboard", error=str(re)), 500
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify(message="Error fetching dashboard data", error=str(e)), 500
