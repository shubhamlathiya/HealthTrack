import datetime
import os

from bson import ObjectId
from flask import jsonify, render_template, request
from werkzeug.utils import secure_filename

from controllers.patients_controllers import patients
from utils.config import mongo
from middleware.auth_middleware import token_required


def object_id_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: object_id_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [object_id_to_str(item) for item in obj]
    return obj


@patients.route("/get-prescription/<appointment_id>", methods=["GET"])
def referred_appointment_id(appointment_id):
    prescription = mongo.db.prescriptions.find_one({"appointment_id": ObjectId(appointment_id)})
    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    # Convert ObjectId to string for JSON serialization
    prescription["_id"] = str(prescription["_id"])
    prescription["appointment_id"] = str(prescription["appointment_id"])
    prescription = object_id_to_str(prescription)

    # print(prescription)
    return jsonify(prescription), 200
    # return jsonify(result), 200


@patients.route('/upload-patient-reports')
def upload_patient_reports():  # put application's code here
    return render_template('patient_templates/upload_view_patient_reports_templates.html')


UPLOAD_FOLDER = 'uploads/patient_reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@patients.route('/upload-report', methods=['POST'], endpoint='upload-report')
@token_required
def upload_patient_report(current_user):
    try:
        # Parse request data
        data = request.form
        file = request.files.get('file')  # Assuming the report file is uploaded
        report_name = data.get('report_name')
        status = data.get('status', 'active')  # Default status set to 'active'
        notes = data.get('notes', '')

        print(data)
        # Validate required fields
        if not all([report_name, file]):
            return jsonify({"error": "patient_id, report_name, and file are required"}), 400

        # Find the patient in the database
        patient = mongo.db.users.find_one({"_id": ObjectId(current_user)})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Generate current date if not provided
        test_date_obj = datetime.datetime.now()

        # Get the original filename extension
        file_extension = file.filename.rsplit('.', 1)[1].lower()

        # Create the new filename with the format: reportname_25_12_2024.ext
        new_filename = f"{report_name}_{current_user}_{test_date_obj.strftime('%d_%m_%Y')}.{file_extension}"

        # Secure the filename
        new_filename = secure_filename(new_filename)

        file_path = f"uploads/patient_reports/{new_filename}"

        # Save the file to the specified path
        file.save(file_path)
        # Set the file path to save (ensure the directory exists)
        # file_path = os.path.join("uploads", "patient_reports", new_filename)
        #
        # # Save the file to the specified path
        # file.save(file_path)

        # Create the report document with the required structure
        report_data = {
            "user_id": ObjectId(current_user),
            "report_name": report_name,
            "status": status,  # Status is set to 'active'
            "file_path": file_path,  # Make sure to return the relative path
            "notes": notes
        }

        # Insert the report into the patient's document
        mongo.db.uploaded_test_reports.insert_one(report_data)

        # Optionally, create an audit log for the action
        audit_log = {
            "user_id": current_user,
            "action": "Upload Report",
            "resource": "Patient Report",
            "timestamp": datetime.datetime.now(),
            "success": True,
            "error_message": None
        }

        # Insert audit log into the collection
        mongo.db.audit_logs.insert_one(audit_log)

        return jsonify({"message": "Patient report uploaded successfully"}), 200

    except Exception as e:
        # On error, create an audit log with error details
        audit_log = {
            "user_id": current_user,
            "action": "Upload Report",
            "resource": "Patient Report",
            "timestamp": datetime.datetime.now(),
            "success": False,
            "error_message": str(e)
        }
        mongo.db.audit_logs.insert_one(audit_log)
        return jsonify({"error": str(e)}), 500


@patients.route('/get-reports/', methods=['GET'], endpoint='get_reports')
@token_required
def get_patient_reports(current_user):
    try:
        # Ensure patient_id is valid (ObjectId format)
        if not ObjectId.is_valid(current_user):
            return jsonify({"error": "Invalid patient ID"}), 400

        # Query the uploaded_test_reports collection to find reports for the patient
        reports = mongo.db.uploaded_test_reports.find({"user_id": ObjectId(current_user)})

        # If no reports are found
        if not reports:
            return jsonify({"message": "No reports found for this patient", "reports": []}), 200

        # Structure the report data to return
        formatted_reports = []
        for report in reports:
            formatted_reports.append({
                "report_name": report.get("report_name"),
                "status": report.get("status"),
                "file_path": report.get("file_path"),
                "notes": report.get("notes"),
                "_id": str(report.get("_id"))  # Return _id as a string for better JSON format
            })

        return jsonify({"reports": formatted_reports}), 200

    except Exception as e:
        # Handle any unexpected errors
        return jsonify({"error": str(e)}), 500
