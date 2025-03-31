# Route to get patient profile
from bson import ObjectId
from flask import jsonify, request, render_template

from controllers.patients_controllers import patients
from utils.config import mongo
from middleware.auth_middleware import token_required


@patients.route('/get-profile', methods=['GET'],endpoint='get_profile')
@token_required
def get_profile(current_user):
    try:
        # Ensure the patient_id is a valid ObjectId
        if not ObjectId.is_valid(current_user):
            return jsonify({"error": "Invalid patient ID"}), 400

        patient = list(mongo.db.users.find({"_id": ObjectId(current_user)}))
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # print(patient)
        # profile_data = {
        #     "patient_id": str(patient["user_id"]),
        #     "name": patient.get("name", "N/A"),
        #     "email": patient.get("email", "N/A"),
        #     "dob": patient.get("dob", "Not Provided"),
        #     "age": patient.get("age", "N/A"),
        #     "address": patient.get("address", "Not Provided"),
        #     "contact_number": patient.get("contact_number", "Not Provided"),
        #     "gender": patient.get("gender", "Not Provided")
        # }
        # return jsonify(profile_data), 200
        return render_template("patient_templates/patient_profile_templates.html", patient=patient)


    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to update patient profile
@patients.route('/update-profile/', methods=['POST'],endpoint='update_profile')
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        updated_data = {
            "name": data["name"],
            "dob": data["dob"],
            "address": data["address"],
            "mobile_number": data["contact_number"],
            "gender": data["gender"]
        }

        if not ObjectId.is_valid(current_user):
            return jsonify({"error": "Invalid patient ID"}), 400

        mongo.db.users.update_one({"_id": ObjectId(current_user)}, {"$set": updated_data})

        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
