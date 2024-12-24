
from flask import jsonify, request
from bson import ObjectId
from datetime import datetime

from api.patients import patients
from config import mongo

@patients.route('/dashboard/<patient_id>', methods=['GET'])
def patient_dashboard(patient_id):
    try:
        # Fetch the patient's document
        patient_document = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})

        if not patient_document:
            return jsonify({"error": "Patient not found"}), 404

        # Appointments Count
        appointments_count = len(patient_document.get("appointments", []))

        # Calculate the total pending amount
        pending_total_amount = mongo.db.bills.aggregate([
            {"$match": {"patient_id": patient_id, "status": "Pending"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        pending_total_amount = next(pending_total_amount, {}).get("total", 0)

        # Number of reports
        reports_count = mongo.db.prescriptions.aggregate([
            {"$match": {"patient_id": ObjectId(patient_id)}},
            {"$project": {"test_report_count": {"$size": "$test_report"}}},
            {"$group": {"_id": None, "total_reports": {"$sum": "$test_report_count"}}}
        ])
        reports_count = next(reports_count, {}).get("total_reports", 0)

        # Number of pending reports
        pending_reports_count = mongo.db.prescriptions.aggregate([
            {"$match": {"patient_id": ObjectId(patient_id)}},
            {"$unwind": "$test_report"},
            {"$match": {"test_report.status": "Pending"}},
            {"$group": {"_id": None, "total_pending": {"$sum": 1}}}
        ])
        pending_reports_count = next(pending_reports_count, {}).get("total_pending", 0)

        # Last appointment details
        last_appointment = max(
            patient_document.get("appointments", []),
            key=lambda x: datetime.strptime(f"{x['date']} {x['time']}", "%Y-%m-%d %H:%M"),
            default=None
        )
        if last_appointment and "_id" in last_appointment:
            last_appointment["_id"] = str(last_appointment["_id"])

        # Fetch the last report details
        last_report = mongo.db.prescriptions.find(
            {"patient_id": patient_id, "test_report": {"$exists": True, "$not": {"$size": 0}}}
        ).sort("date", -1).limit(1)
        last_report = next(last_report, None)

        if last_report:
            last_report["_id"] = str(last_report["_id"])
            for report in last_report.get("test_report", []):
                if "report_id" in report:
                    report["report_id"] = str(report["report_id"])

        # Prepare the response
        response = {
            "appointments_count": appointments_count,
            "pending_total_amount": pending_total_amount,
            "reports_count": reports_count,
            "pending_reports_count": pending_reports_count,
            "last_appointment": last_appointment,
            "last_report": {
                "prescription_id": str(last_report["_id"]) if last_report else None,
                "test_reports": last_report["test_report"] if last_report else None,
                "date": last_report["date"].strftime("%Y-%m-%d %H:%M:%S") if last_report else None
            }
        }

        return jsonify(str(response)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
