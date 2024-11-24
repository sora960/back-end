# speed_test.py (Make sure it's imported correctly)
from flask import Blueprint, jsonify, current_app, render_template
import speedtest as speedtest_cli
from datetime import datetime
import logging
from utils import log_activity  # Import the log_activity function

# Initialize blueprint for speedtest
speedtest_bp = Blueprint('speedtest', __name__)

# Logger setup
logger = logging.getLogger(__name__)

@speedtest_bp.route('/speedtest')  # Use '/speedtest' as the URL for rendering the speed test page
def render_speedtest_page():
    """Render the speed test page."""
    return render_template('speedtest.html')  # This renders the HTML page with the Run Speed Test button

@speedtest_bp.route('/api/run-speed-test', methods=['GET'])
def run_speed_test():
    """Conducts a speed test and returns the result."""
    try:
        # Initialize the speed test
        st = speedtest_cli.Speedtest()
        st.get_best_server()  # Get the best server based on location
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        ping = st.results.ping
        timestamp = datetime.utcnow().isoformat() + "Z"  # ISO format timestamp

        # Prepare speed test data
        speed_test_data = {
            "download_speed": download_speed,
            "upload_speed": upload_speed,
            "ping": ping,
            "timestamp": timestamp
        }

        # Store the results in MongoDB
        mongo = current_app.extensions['pymongo']
        result = mongo.db.speed_tests.insert_one(speed_test_data)  # Insert into the speed_tests collection
        speed_test_data['_id'] = str(result.inserted_id)  # Convert MongoDB ObjectId to string

        # **Log the activity for speed test**
        log_activity("Speed Test", f"Ran speed test with download speed: {download_speed:.2f} Mbps and upload speed: {upload_speed:.2f} Mbps")

        # Log and return the result
        logger.info(f"Speed test completed. Download: {download_speed:.2f} Mbps, Upload: {upload_speed:.2f} Mbps")
        return jsonify(message="Speed test completed!", results=speed_test_data)

    except Exception as e:
        # Handle any exceptions and log the error
        logger.error(f"Error conducting speed test: {str(e)}")
        return jsonify(message="Error conducting speed test", error=str(e)), 500
