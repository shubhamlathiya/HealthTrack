import datetime
import os

from bson import ObjectId
from flask import jsonify, render_template, request
from werkzeug.utils import secure_filename

from controllers.laboratory_controllers import laboratory
from utils.config import mongo


def serialize_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


@laboratory.route('/prescriptions-pending-test-reports', methods=['GET'])
def get_prescriptions():
    try:
        # Aggregate query to fetch prescriptions with "pending" status_reports
        pipeline = [
            {"$match": {"test_reports.status_reports": "pending"}},  # Filter for "pending" status_reports
            {
                "$lookup": {
                    "from": "appointments",  # Appointment collection
                    "localField": "appointment_id",  # Field in prescriptions
                    "foreignField": "_id",  # Field in appointments to match
                    "as": "appointment_details"  # Include matched appointment details
                }
            },
            {
                "$unwind": "$appointment_details"  # Flatten the appointment_details array
            },
            {
                "$lookup": {
                    "from": "users",  # User collection for patient details
                    "localField": "appointment_details.patient_id",  # Patient reference
                    "foreignField": "_id",  # Field in users (patients)
                    "as": "patient_details"  # Include matched patient details
                }
            },
            {
                "$unwind": "$patient_details"  # Flatten the patient_details array
            },
            {
                "$lookup": {
                    "from": "users",  # User collection for doctor details
                    "localField": "appointment_details.doctor_id",  # Doctor reference
                    "foreignField": "_id",  # Field in users (doctors)
                    "as": "doctor_details"  # Include matched doctor details
                }
            },
            {
                "$unwind": "$doctor_details"  # Flatten the doctor_details array
            },
            {
                "$project": {
                    "_id": 1,
                    "appointment_id": 1,
                    "test_reports": 1,
                    "patient_name": "$patient_details.name",
                    "patient_email": "$patient_details.email",
                    "patient_contact": "$patient_details.mobile_number",
                    # assuming this field exists in patient details
                    "doctor_name": "$doctor_details.name",
                    "doctor_email": "$doctor_details.email",
                    "doctor_contact": "$doctor_details.mobile_number",  # assuming this field exists in doctor details
                    "test_reports_report_name": {"$arrayElemAt": ["$test_reports.report_name", 0]},
                    # Get the first report name
                    "test_reports_price": {"$arrayElemAt": ["$test_reports.price", 0]},  # Get the first report price
                    "test_reports_report_notes": {"$arrayElemAt": ["$test_reports.report_notes", 0]},
                    # Get the first report notes
                    "test_reports_status_reports": {"$arrayElemAt": ["$test_reports.status_reports", 0]}
                    # Get the first status report
                }
            }
        ]

        # Execute aggregation pipeline
        prescriptions = list(mongo.db.prescriptions.aggregate(pipeline))

        # Before the for loop, the data fetched will look like the following:
        # print("Before For Loop:")
        # print(prescriptions)

        # Convert ObjectId to string for JSON serialization
        for prescription in prescriptions:
            prescription['_id'] = str(prescription['_id'])  # Serialize ObjectId to string
            prescription['appointment_id'] = str(prescription['appointment_id'])  # Serialize appointment_id

            # Now handle multiple test_reports, ensuring we correctly include each report's details
            test_reports = []
            for report in prescription['test_reports']:
                test_reports.append({
                    'report_id': str(report.get('report_id', '')),
                    'test_reports_report_name': report.get('report_name', ''),  # From prescriptions collection
                    'test_reports_price': report.get('price', 0),  # From prescriptions collection
                    'report_notes': report.get('report_notes', ''),  # From prescriptions collection
                    'status_reports': report.get('status_reports', '')  # From prescriptions collection
                })
            prescription['test_reports'] = test_reports  # Set all reports in the test_reports field

            # Ensure patient and doctor fields are correct
            prescription['patient_name'] = prescription.get('patient_name', '')
            prescription['patient_email'] = prescription.get('patient_email', '')
            prescription['patient_contact'] = prescription.get('patient_contact', '')
            prescription['doctor_name'] = prescription.get('doctor_name', '')
            prescription['doctor_email'] = prescription.get('doctor_email', '')
            prescription['doctor_contact'] = prescription.get('doctor_contact', '')

        # After the for loop, the data will look like the desired format:
        # print("After For Loop:")
        # print(prescriptions)
        if not prescriptions:
            return render_template('laboratory_templates/patient_test_report_management_templates.html',
                                   error="No found Reports")

        # Return the prescriptions with matching appointment, patient, doctor, and test report details
        return render_template("laboratory_templates/patient_test_report_management_templates.html",
                               prescriptions=prescriptions), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "Internal server error"}), 500


UPLOAD_FOLDER = 'uploads/reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}


# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@laboratory.route('/upload-test-report', methods=['POST'])
def upload_test_report():
    # try:
    file = request.files.get('file')  # Assuming the report file is uploaded

    # Check if a file is provided
    if not file or file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Extract other required fields
    prescription_id = request.form.get('prescription_id')
    report_id = request.form.get('report_id')  # The report_id for which file path needs to be updated
    status = request.form.get('status', 'Completed')

    # print(request.form)
    # Validate required fields
    if not all([prescription_id, report_id]):
        return jsonify({"error": "prescription_id and report_id are required"}), 400

    # Find the prescription
    prescription = mongo.db.prescriptions.find_one({"_id": ObjectId(prescription_id)})
    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    # Verify if the report_id exists in the test_report array of the prescription
    report = next((r for r in prescription.get("test_reports", []) if str(r["report_id"]) == report_id), None)
    if not report:
        return jsonify({"error": f"Report with ID {report_id} not found in the prescription's test reports"}), 404

    # Get the current date for the report (if no specific date provided by user)
    test_date_obj = datetime.datetime.now()

    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file format. Allowed formats are: pdf, docx, jpg, jpeg, png."}), 400

    # Get the original filename extension
    file_extension = file.filename.rsplit('.', 1)[1].lower()

    # Create the new filename with the format: reportname_25_12_2024.ext
    new_filename = f"test_report_{prescription_id}_{report_id}_{test_date_obj.strftime('%d_%m_%Y')}.{file_extension}"

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
        {"_id": ObjectId(prescription_id), "test_reports.report_id": ObjectId(report_id)},
        {
            "$set": {
                "test_reports.$.status_reports": status,
                "test_reports.$.file_path": file_path,
            }
        }
    )

    # Notify doctor and patient (Optional: Add notification logic here)

    return jsonify({"message": "Test report uploaded and updated successfully"}), 200

# except Exception as e:
#     return jsonify({"error": str(e)}), 500
