from datetime import datetime

from flask import jsonify, request, render_template

from controllers.laboratory_controllers import laboratory
from utils.config import mongo


@laboratory.route('/add-reports', methods=['GET', 'POST'])
def add_report():
    if request.method == 'POST':
        try:
            report_name = request.form.get("report_name")
            description = request.form.get("description")
            price = request.form.get("price")
            # Default status is Active

            if not report_name or not description or not price:
                return jsonify({"error": "All fields are required."}), 400

            existing_lab_reports = mongo.db.lab_reports.find_one({'report_name': report_name})
            if existing_lab_reports:
                return jsonify({'error': 'report already existing'}), 400
                # Convert price to a float if it's a valid number
            try:
                price = float(price)
            except ValueError:
                return jsonify({"error": "Invalid price."}), 400

            report_data = {
                "report_name": report_name,
                "description": description,
                "price": price,
                "status": True,  # Default status
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            mongo.db.lab_reports.insert_one(report_data)

            return jsonify({"message": "Report added successfully"}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == 'GET':
        return render_template('laboratory_templates/add_test_report_templates.html')


@laboratory.route('/get-reports', methods=['GET'])
def get_reports():
    reports = list(mongo.db.lab_reports.find())

    if not reports:
        return jsonify({"error": "No reports found."}), 400

    for report in reports:
        if '_id' in report:
            report['_id'] = str(report['_id'])  # Convert ObjectId to string

    return jsonify({"reports": reports}), 200



