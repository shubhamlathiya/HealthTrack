from bson import ObjectId
from flask import jsonify,request

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
