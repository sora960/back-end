import psutil
from flask import Blueprint, jsonify, current_app, render_template
from datetime import datetime
from utils import log_activity, logger, handle_database_error, log_route

# Initialize the blueprint
data_usage = Blueprint('data_usage', __name__)

@data_usage.route('/data_usage', methods=['GET'])
@log_route  # Log this route
def render_data_usage_page():
    """Render the data usage page."""
    try:
        logger.info("Rendering data usage page.")
        return render_template('data_usage.html')
    except Exception as e:
        logger.error(f"Error rendering data usage page: {e}")
        return handle_database_error("Error rendering data usage page.")

@data_usage.route('/track-data-usage', methods=['POST'])
@log_route  # Log this route
def track_data_usage():
    """Fetches real-time data usage for the current device and logs it in the database."""
    try:
        # Log the start of the process
        logger.info("Starting data usage tracking...")

        # Use psutil to get network I/O statistics
        net_io = psutil.net_io_counters()

        # Convert bytes to MB
        download = round(net_io.bytes_recv / (1024 * 1024), 2)
        upload = round(net_io.bytes_sent / (1024 * 1024), 2)
        timestamp = datetime.utcnow().isoformat() + "Z"
        day_of_week = datetime.utcnow().strftime('%A')  # Current day (e.g., "Monday")

        # Prepare the data usage record
        data_usage_record = {
            "day": day_of_week,
            "download": download,
            "upload": upload,
            "timestamp": timestamp
        }

        # Store the data usage record in the data_usage collection
        mongo = current_app.extensions.get('pymongo')
        if mongo:
            result = mongo.db.data_usage.insert_one(data_usage_record)
            data_usage_record["_id"] = str(result.inserted_id)  # Convert ObjectId to string
            logger.info(f"Data usage stored in MongoDB with ID: {data_usage_record['_id']}")
        else:
            logger.warning("MongoDB is not initialized. Skipping data usage storage.")

        # Log the activity to the activities collection
        log_activity(
            "Data Usage Tracking",
            {
                "day": day_of_week,
                "download": download,
                "upload": upload,
                "timestamp": timestamp
            }
        )
        logger.info(f"Data usage activity logged successfully: {data_usage_record}")

        # Return the result
        return jsonify(message="Data usage tracked successfully!", data_usage=data_usage_record)

    except Exception as e:
        # Handle exceptions and log the error
        logger.error(f"Error tracking data usage: {e}")
        log_activity(
            "Data Usage Tracking Error",
            {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        return handle_database_error(f"Error tracking data usage: {e}")
