from bson import ObjectId
from flask import render_template, jsonify

from api.admin import admin
from api.doctor import doctors
from config import mongo
from middleware.auth_middleware import token_required

def objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [objectid_to_str(v) for v in obj]
    else:
        return obj

@doctors.route('/dashboard' , methods=['GET'])
def dashboard():
    return render_template("doctor/doctor_dashboard_templets.html")

@doctors.route('/get-patient-details/<patient_id>', methods=['GET'] , endpoint='get_patient_details')
@token_required
def get_patient_data(current_user , patient_id):
    try:
        # Fetch user details by patient_id (which corresponds to user_id in the database)
        user = mongo.db.users.find_one({"user_id": patient_id})

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Fetch appointments for the given user
        appointments = list(mongo.db.appointments.find({"patient_id": ObjectId(user['_id'])}))

        # Fetch uploaded test reports for the given user
        uploaded_test_reports = list(mongo.db.uploaded_test_reports.find({"user_id": ObjectId(user['_id'])}))

        # Fetch prescriptions related to the user's appointments
        appointment_ids = [a["_id"] for a in appointments]
        prescriptions = list(mongo.db.prescriptions.find({"appointment_id": {"$in": appointment_ids}}))

        # Prepare the response data
        patient_data = {
            "user": {
                "_id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "gender" : user.get("gender"),
                "mobile_number" : user.get("mobile_number"),
                "address": user.get("address"),
            },
            "appointments": objectid_to_str(appointments),
            "uploadedTestReports": objectid_to_str(uploaded_test_reports),
            "prescriptions": objectid_to_str(prescriptions),
        }

        # print(patient_data)
        # Return the data in JSON format
        return jsonify(patient_data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500