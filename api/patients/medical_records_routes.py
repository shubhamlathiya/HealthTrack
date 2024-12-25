import datetime
import os

from bson import ObjectId
from flask import jsonify,request
from werkzeug.utils import secure_filename

from api.patients import patients
from config import mongo


@patients.route('/medical-records/<patient_id>', methods=['GET'])
def get_medical_records(patient_id):
    # Find the patient
    patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    # Return medical records
    medical_records = patient.get('medical_records', [])
    return jsonify({"medical_records": medical_records}), 200

UPLOAD_FOLDER = 'uploads/patient_reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@patients.route('/upload-report', methods=['POST'])
def upload_patient_report():
    try:
        # Parse request data
        data = request.form
        file = request.files.get('file')  # Assuming the report file is uploaded
        patient_id = data.get('patient_id')
        report_name = data.get('report_name')
        status = data.get('status', 'Completed')
        additional_details = data.get('additional_details', '')
        notes = data.get('notes', '')

        # Validate required fields
        if not all([patient_id, report_name, file]):
            return jsonify({"error": "patient_id, report_name, and file are required"}), 400

        # Find the patient in the database
        patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Generate current date if not provided
        try:
            test_date_obj = datetime.datetime.now()
        except ValueError:
            return jsonify({"error": "Invalid date format, use DD-MM-YYYY"}), 400

        # Get the original filename extension
        file_extension = file.filename.rsplit('.', 1)[1].lower()

        # Create the new filename with the format: reportname_25_12_2024.ext
        new_filename = f"{report_name}_{patient_id}_{test_date_obj.strftime('%d_%m_%Y')}.{file_extension}"

        # Secure the filename
        new_filename = secure_filename(new_filename)

        # Set the file path to save (ensure the directory exists)
        file_path = os.path.join("uploads", "patient_reports", new_filename)

        # Save the file to the specified path
        file.save(file_path)

        # Create audit log
        audit_log = {
            "user_id": patient_id,
            "action": "Upload Report",
            "resource": "Patient Report",
            "timestamp": datetime.datetime.now(),
            "success": True,
            "error_message": None
        }

        # Insert audit log into the collection
        mongo.db.audit_logs.insert_one(audit_log)

        # Update patient's report details (Assuming there is a field for reports)
        mongo.db.patients.update_one(
            {"_id": ObjectId(patient_id)},
            {
                "$push": {
                    "upload_test_reports": {
                        "report_name": report_name,
                        "result_time": datetime.datetime.now(),
                        "status": status,
                        "additional_details": additional_details,
                        "notes": notes,
                        "file_path": file_path
                    }
                }
            }
        )

        return jsonify({"message": "Patient report uploaded successfully"}), 200

    except Exception as e:
        # On error, create an audit log with error details
        audit_log = {
            "user_id": patient_id,
            "action": "Upload Report",
            "resource": "Patient Report",
            "timestamp": datetime.datetime.now(),
            "success": False,
            "error_message": str(e)
        }
        mongo.db.audit_logs.insert_one(audit_log)
        return jsonify({"error": str(e)}), 500