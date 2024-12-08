from flask import Blueprint, jsonify, current_app, render_template
from datetime import datetime
import logging
from bson import ObjectId

# Initialize the blueprint
report = Blueprint('report', __name__)

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def format_time_and_date(timestamp):
    """
    Convert a timestamp into a human-readable format for reports.
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", ""))
        return dt.strftime("%I:%M %p %B %d, %Y")
    except Exception as e:
        logger.error(f"Error formatting timestamp: {timestamp}, Error: {e}")
        return "Unknown Time"

def migrate_activities_to_reports():
    """
    Reads the `activities` collection, checks for existing records in `reports`, 
    and migrates only new activities to `reports`.
    """
    try:
        mongo = current_app.extensions['pymongo']

        # Check if there are any activities to migrate
        if mongo.db.activities.count_documents({}) == 0:
            logger.info("No activities to migrate.")
            return

        # Fetch already migrated activity IDs from reports
        migrated_activity_ids = set(
            report["activity_id"] for report in mongo.db.reports.find({}, {"_id": 0, "activity_id": 1})
        )

        # Iterate over activities and process new ones
        for activity in mongo.db.activities.find():
            activity_id = str(activity["_id"])  # Convert ObjectId to string

            if activity_id in migrated_activity_ids:
                logger.debug(f"Activity with ID {activity_id} already migrated. Skipping.")
                continue  # Skip already migrated activities

            action = activity.get("action")
            timestamp = activity.get("timestamp", "")
            details = activity.get("details", {})

            # Handle missing fields
            if not timestamp:
                logger.warning(f"Activity {activity_id} missing timestamp. Skipping.")
                continue
            if not action:
                logger.warning(f"Activity {activity_id} missing action type. Skipping.")
                continue

            # Ensure details is a dictionary
            if isinstance(details, str):
                logger.warning(f"Details field is a string. Converting to dictionary: {details}")
                details = {"message": details}

            # Map actions to report types and details
            if action == "IP Assignment":
                report_type = "IP Assignment"
                report_details = f"Assigned IP {details.get('ip_address', 'N/A')} to device with MAC {details.get('mac_address', 'N/A')}."
            elif action == "Device Block":
                report_type = "Device Blocked"
                report_details = f"Blocked MAC {details.get('mac_address', 'N/A')}."
            elif action == "Device Unblock":
                report_type = "Device Unblocked"
                report_details = f"Unblocked MAC {details.get('mac_address', 'N/A')}."
            elif action == "Data Usage Tracking":
                report_type = "Data Usage"
                report_details = f"Tracked data usage: Download={details.get('download', 0)} MB, Upload={details.get('upload', 0)} MB."
            elif action == "Speed Test":
                report_type = "Speed Test"
                report_details = (
                    f"Speed test results: Download speed={details.get('download_speed', 0)} Mbps, "
                    f"Upload speed={details.get('upload_speed', 0)} Mbps, Ping={details.get('ping', 0)} ms."
                )
            else:
                logger.warning(f"Unrecognized action type: {action}")
                continue  # Skip invalid actions

            # Prepare the report document
            report = {
                "activity_id": activity_id,  # Add reference to the original activity
                "report_type": report_type,
                "time_and_date": format_time_and_date(timestamp),
                "details": report_details
            }

            # Insert into the `reports` collection
            try:
                mongo.db.reports.insert_one(report)
                logger.info(f"Report logged: {report}")
            except Exception as db_error:
                logger.error(f"Failed to log report for activity ID {activity_id}: {db_error}")

        logger.info("Migration of activities to reports completed successfully.")

    except Exception as e:
        logger.error(f"Error during migration of activities to reports: {e}")

@report.route('/run_migration', methods=['POST'])
def run_migration():
    """
    Trigger the migration of data from `activities` to `reports`.
    """
    try:
        migrate_activities_to_reports()
        return jsonify(message="Migration completed successfully."), 200
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return jsonify(message="Migration failed.", error=str(e)), 500

@report.route('/generate_report', methods=['POST'])
def generate_report():
    """
    Placeholder for the generate report functionality.
    """
    return jsonify(message="Generate report functionality is under construction."), 200

@report.route('/report', methods=['GET'])
def render_report_page():
    """
    Render the report page for front-end usage.
    """
    try:
        return render_template('report.html')
    except Exception as e:
        logger.error(f"Error rendering report page: {e}")
        return jsonify(message="Error rendering report page.", error=str(e)), 500
    

@report.route('/api/reports', methods=['GET'])
def get_reports():
    """
    Fetch all reports from the database and return as JSON.
    """
    try:
        mongo = current_app.extensions['pymongo']
        reports_cursor = mongo.db.reports.find({}, {"_id": 0})  # Exclude ObjectId
        reports = list(reports_cursor)  # Convert cursor to list
        return jsonify(reports=reports), 200
    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        return jsonify(error="Failed to fetch reports."), 500

