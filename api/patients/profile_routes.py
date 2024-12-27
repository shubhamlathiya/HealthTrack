# Route to get patient profile
from bson import ObjectId
from flask import jsonify,request

from api.patients import patients
from config import mongo


@patients.route('/get-profile/<patient_id>', methods=['GET'])
def get_profile(patient_id):
    try:
        # Ensure the patient_id is a valid ObjectId
        if not ObjectId.is_valid(patient_id):
            return jsonify({"error": "Invalid patient ID"}), 400

        patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        profile_data = {
            "patient_id": str(patient["patient_id"]),
            "name": patient.get("name", "N/A"),
            "email": patient.get("email", "N/A"),
            "dob": patient.get("dob", "Not Provided"),
            "age": patient.get("age", "N/A"),
            "address": patient.get("address", "Not Provided"),
            "contact_number": patient.get("contact_number", "Not Provided"),
            "gender": patient.get("gender", "Not Provided")
        }
        return jsonify(profile_data), 200


    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to update patient profile
@patients.route('/update-profile/<patient_id>', methods=['POST'])
def update_profile(patient_id):
    try:
        data = request.get_json()
        updated_data = {
            "name": data["name"],
            "email": data["email"],
            "dob": data["dob"],
            "age": data["age"],
            "address": data["address"],
            "contact_number": data["contact_number"],
            "gender": data["gender"]
        }

        if not ObjectId.is_valid(patient_id):
            return jsonify({"error": "Invalid patient ID"}), 400

        mongo.db.patients.update_one({"_id": ObjectId(patient_id)}, {"$set": updated_data})

        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
