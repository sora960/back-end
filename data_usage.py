import psutil
from flask import Blueprint, jsonify, current_app, render_template
import logging
from datetime import datetime

# Initialize the blueprint
data_usage = Blueprint('data_usage', __name__)

# Logger setup
logger = logging.getLogger(__name__)

# Render Data Usage Page
@data_usage.route('/data_usage')
def render_data_usage_page():
    return render_template('data_usage.html')


# Route to track and store real-time data usage for the current device
@data_usage.route('/track-data-usage', methods=['POST'])
def track_data_usage():
    """Fetches real-time data usage for the current device and stores it in the database."""
    try:
        # Use psutil to get network I/O statistics
        net_io = psutil.net_io_counters()

        # Convert bytes to MB
        download = net_io.bytes_recv / (1024 * 1024)
        upload = net_io.bytes_sent / (1024 * 1024)

        # Get current UTC timestamp and day of the week
        timestamp = datetime.utcnow().isoformat() + "Z"
        day_of_week = datetime.utcnow().strftime('%A')  # Current day (e.g., "Monday")

        # Prepare the data usage record
        data_usage_record = {
            "day": day_of_week,
            "download": round(download, 2),  # Rounding the download to 2 decimal places
            "upload": round(upload, 2),      # Rounding the upload to 2 decimal places
            "timestamp": timestamp
        }

        # Access mongo via current_app
        mongo = current_app.extensions['pymongo']  # Get the MongoDB instance

        # Insert data usage into the database
        result = mongo.db.data_usage.insert_one(data_usage_record)

        # Convert ObjectId to string for JSON serialization
        data_usage_record["_id"] = str(result.inserted_id)

        logger.info(f"Data usage tracked: {data_usage_record}")

        # Return the result with the stringified ObjectId
        return jsonify(message="Real-time data usage tracked successfully!", data_usage=data_usage_record)

    except Exception as e:
        logger.error(f"Error tracking data usage: {str(e)}")
        return jsonify(message="Error tracking data usage", error=str(e)), 500
