from flask import Blueprint, jsonify, render_template, current_app
import speedtest
from datetime import datetime
from utils import log_activity, logger, handle_database_error, log_route

# Initialize blueprint for speedtest
speedtest_bp = Blueprint('speedtest', __name__)

@speedtest_bp.route('/speedtest', methods=['GET'])
@log_route  # Log this route
def render_speedtest_page():
    """Render the speed test page."""
    try:
        logger.info("Rendering speed test page.")
        return render_template('speedtest.html')  # Renders the HTML page with the Run Speed Test button
    except Exception as e:
        logger.error(f"Error rendering speed test page: {e}")
        return handle_database_error("Error rendering speed test page.")

@speedtest_bp.route('/api/run-speed-test', methods=['GET'])
@log_route  # Log this route
def run_speed_test():
    """Conducts a speed test and returns the result."""
    try:
        # Initialize the speed test
        logger.info("Starting speed test...")
        st = speedtest.Speedtest()
        st.get_best_server()  # Get the best server based on location
        
        # Validate server information
        server = (
            st.results.server['host'] 
            if st.results.server and 'host' in st.results.server 
            else 'Unknown'
        )
        
        # Run the speed test
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        ping = st.results.ping
        timestamp = datetime.utcnow().isoformat() + "Z"  # ISO format timestamp

        # Prepare speed test data
        speed_test_data = {
            "download_speed": round(download_speed, 2),
            "upload_speed": round(upload_speed, 2),
            "ping": round(ping, 2),
            "server": server,
            "timestamp": timestamp
        }

        logger.info(f"Speed test completed successfully. Results: {speed_test_data}")

        # Store the results in MongoDB
        mongo = current_app.extensions.get('pymongo')
        if mongo:
            try:
                result = mongo.db.speed_tests.insert_one(speed_test_data)
                speed_test_data['_id'] = str(result.inserted_id)  # Convert ObjectId to string
                logger.info(f"Speed test data stored in MongoDB with ID: {speed_test_data['_id']}")
            except Exception as db_error:
                logger.error(f"Error storing speed test data in MongoDB: {db_error}")
        else:
            logger.warning("MongoDB is not initialized. Skipping data storage.")

        # Log the activity for speed test
        try:
            log_activity(
                "Speed Test",
                {
                    "download_speed": round(download_speed, 2),
                    "upload_speed": round(upload_speed, 2),
                    "ping": round(ping, 2),
                    "server": server,
                    "timestamp": timestamp
                }
            )
            logger.info("Speed test activity logged successfully.")
        except Exception as log_error:
            logger.warning(f"Failed to log speed test activity: {log_error}")

        # Return the result
        return jsonify(message="Speed test completed!", results=speed_test_data)

    except Exception as e:
        # Handle exceptions and log the error
        logger.error(f"Error conducting speed test: {e}")
        try:
            log_activity(
                "Speed Test Error",
                {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        except Exception as log_error:
            logger.warning(f"Failed to log speed test error: {log_error}")

        return handle_database_error(f"Error conducting speed test: {e}")
