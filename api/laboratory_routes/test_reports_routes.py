import datetime
import os

from bson import ObjectId
from flask import jsonify,request
from werkzeug.utils import secure_filename

from api.laboratory_routes import laboratory
from config import mongo


@laboratory.route('/get-test-reports', methods=['GET'])
def get_test_reports():
    # Query parameters for filtering
    patient_id = request.args.get('patient_id')  # Optional patient ID to filter reports
    doctor_id = request.args.get('doctor_id')    # Optional doctor ID to filter reports
    status = request.args.get('status')          # Optional status (e.g., Pending, Completed)
    report_name = request.args.get('report_name')  # Optional report name for specific reports

    # Build the query dynamically based on provided filters
    query = {}
    if patient_id:
        query["patient_id"] = ObjectId(patient_id)
    if doctor_id:
        query["doctor_id"] = ObjectId(doctor_id)
    if status:
        query["test_report.status"] = status
    if report_name:
        query["test_report.report_name"] = report_name

    # Fetch reports matching the query
    reports = mongo.db.prescriptions.find(query, {"test_report": 1, "patient_id": 1, "doctor_id": 1, "date": 1})

    # Format the response
    result = []
    for report in reports:
        formatted_reports = [
            {
                "report_name": test.get("report_name"),
                "result_time": test.get("result_time"),
                "additional_details": test.get("additional_details"),
                "status": test.get("status"),
                "notes": test.get("notes")
            }
            for test in report.get("test_report", [])
        ]
        result.append({
            "prescription_id": str(report["_id"]),
            "patient_id": str(report.get("patient_id")),
            "doctor_id": str(report.get("doctor_id")),
            "date": report.get("date"),
            "test_reports": formatted_reports
        })

    return jsonify({"test_reports": str(result)}), 200


# Directory to save uploaded files
UPLOAD_FOLDER = 'uploads/reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_FOLDER = "uploads/reports"
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@laboratory.route('/upload-test-report', methods=['POST'])
def upload_test_report():
    try:
        # Parse request data
        data = request.form
        file = request.files.get('file')  # Assuming the report file is uploaded

        # Check if a file is actually provided
        if not file or file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Extract other required fields
        prescription_id = data.get('prescription_id')
        report_name = data.get('report_name')
        status = data.get('status', 'Completed')
        additional_details = data.get('additional_details', '')
        notes = data.get('notes', '')

        # Validate required fields
        if not all([prescription_id, report_name]):
            return jsonify({"error": "prescription_id, report_name are required"}), 400

        # Find the prescription
        prescription = mongo.db.prescriptions.find_one({"_id": ObjectId(prescription_id)})
        if not prescription:
            return jsonify({"error": "Prescription not found"}), 404

            # Fetch the patient_id from the prescription
        patient_id = prescription.get("patient_id")
        if not patient_id:
            return jsonify({"error": "patient_id not found in prescription"}), 400

        # Verify if report_name exists in test_report
        report = next((r for r in prescription.get("test_report", []) if r["report_name"] == report_name), None)
        if not report:
            return jsonify({"error": f"Report name '{report_name}' not found in the prescription's test reports"}), 404

        # Get the current date for the report (if no specific date provided by user)
        test_date_obj = datetime.datetime.now()

        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file format. Allowed formats are: pdf, docx, jpg, jpeg, png."}), 400

        # Get the original filename extension
        file_extension = file.filename.rsplit('.', 1)[1].lower()

        # Create the new filename with the format: reportname_25_12_2024.ext
        new_filename = f"{report_name}_{patient_id}_{test_date_obj.strftime('%d_%m_%Y')}.{file_extension}"

        # Secure the filename
        new_filename = secure_filename(new_filename)

        # Ensure the upload directory exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # Set the file path to save
        file_path = f"uploads/reports/{new_filename}"

        # Save the file to the specified path
        file.save(file_path)

        # Update the specific report in the prescription's test_report array
        mongo.db.prescriptions.update_one(
            {"_id": ObjectId(prescription_id), "test_report.report_name": report_name},
            {
                "$set": {
                    "test_report.$.result_time": test_date_obj,
                    "test_report.$.status": status,
                    "test_report.$.file_path": file_path,
                    "test_report.$.additional_details": additional_details,
                    "test_report.$.notes": notes
                }
            }
        )

        # Notify doctor and patient (Optional: Add notification logic here)

        return jsonify({"message": "Test report updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500