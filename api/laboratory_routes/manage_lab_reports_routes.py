from datetime import datetime

from flask import jsonify,request

from api.laboratory_routes import laboratory
from config import mongo


@laboratory.route('/lab/reports', methods=['POST'])
def add_report():
    data = request.get_json()
    report_name = data.get('report_name')
    description = data.get('description')
    status = data.get('status', 'Active')  # Default status is Active

    if not report_name:
        return jsonify({"error": "Report name is required"}), 400

    new_report = {
        "report_name": report_name,
        "description": description,
        "status": status,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    report_id = mongo.db.lab_reports.insert_one(new_report).inserted_id

    return jsonify({"message": "Report added successfully", "report_id": str(report_id)}), 201


@laboratory.route('/lab/reports', methods=['GET'])
def get_all_reports():
    reports = list(mongo.db.lab_reports.find({}, {"_id": 0}))
    return jsonify(reports), 200
