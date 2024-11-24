from flask import Blueprint, jsonify, request, current_app, render_template
from datetime import datetime
import logging
from bson import ObjectId

# Initialize the blueprint
report = Blueprint('report', __name__)

# Logger setup
logger = logging.getLogger(__name__)

# Function to convert MongoDB ObjectId and datetime fields to JSON serializable data
def convert_to_serializable(data):
    for entry in data:
        if isinstance(entry.get('_id'), ObjectId):
            entry['_id'] = str(entry['_id'])
        if 'allocated_time' in entry and isinstance(entry['allocated_time'], datetime):
            entry['allocated_time'] = entry['allocated_time'].strftime('%Y-%m-%d %H:%M:%S')
        if 'timestamp' in entry and isinstance(entry['timestamp'], datetime):
            entry['timestamp'] = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    return data

# Render the report page for front-end usage
@report.route('/report')
def render_report_page():
    return render_template('report.html')

# Speed Test Report Route
@report.route('/generate_speed_test_report', methods=['POST'])
def generate_speed_test_report():
    try:
        mongo = current_app.extensions['pymongo']

        # Fetch all Speed Test data
        result = mongo.db.speed_tests.find({})
        report_data = [{"date": entry['timestamp'], "ping": entry['ping'], "download_speed": entry['download_speed'], "upload_speed": entry['upload_speed']} for entry in result]

        if len(report_data) == 0:
            logger.info("No speed test data found.")
            return jsonify(message="No data found"), 200

        # Convert data to a serializable format for JSON response
        report_data = convert_to_serializable(report_data)
        return jsonify(report_data=report_data), 200

    except Exception as e:
        logger.error(f"Error generating speed test report: {str(e)}")
        return jsonify(message="Error generating speed test report", error=str(e)), 500

# IP Allocation Report Route
@report.route('/generate_ip_allocation_report', methods=['POST'])
def generate_ip_allocation_report():
    try:
        mongo = current_app.extensions['pymongo']

        # Fetch all IP Allocation data
        result = mongo.db.ip_allocations.find({})
        report_data = [{"date": entry['allocated_time'], "ip_address": entry['ip_address'], "device_name": entry['device_name']} for entry in result]

        if len(report_data) == 0:
            logger.info("No IP allocation data found.")
            return jsonify(message="No data found"), 200

        # Convert data to a serializable format for JSON response
        report_data = convert_to_serializable(report_data)
        return jsonify(report_data=report_data), 200

    except Exception as e:
        logger.error(f"Error generating IP allocation report: {str(e)}")
        return jsonify(message="Error generating IP allocation report", error=str(e)), 500

# Data Usage Report Route
@report.route('/generate_data_usage_report', methods=['POST'])
def generate_data_usage_report():
    try:
        mongo = current_app.extensions['pymongo']

        # Fetch all Data Usage data
        result = mongo.db.data_usage.find({})
        report_data = [{"date": entry['timestamp'], "day": entry['day'], "download": entry['download'], "upload": entry['upload']} for entry in result]

        if len(report_data) == 0:
            logger.info("No data usage data found.")
            return jsonify(message="No data found"), 200

        # Convert data to a serializable format for JSON response
        report_data = convert_to_serializable(report_data)
        return jsonify(report_data=report_data), 200

    except Exception as e:
        logger.error(f"Error generating data usage report: {str(e)}")
        return jsonify(message="Error generating data usage report", error=str(e)), 500
