from bson import ObjectId
from flask import jsonify

from api.patients import patients
from config import mongo


@patients.route("/get_prescription_all/<patient_id>", methods=["GET"])
def get_prescription_all(patient_id):
    prescription = mongo.db.prescriptions.find_one({"patient_id": ObjectId(patient_id)})
    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    # Convert ObjectId to string for JSON serialization
    prescription["_id"] = str(prescription["_id"])
    prescription["doctor_id"] = str(prescription["doctor_id"])
    prescription["patient_id"] = str(prescription["patient_id"])
    prescription["referred_appointment_id"] = str(prescription["referred_appointment_id"])

    # print(prescription)
    return jsonify(prescription), 200


@patients.route("/get_prescription/<referred_appointment_id>", methods=["GET"])
def referred_appointment_id(referred_appointment_id):
    prescription = mongo.db.prescriptions.find_one({"referred_appointment_id": referred_appointment_id})
    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    # Convert ObjectId to string for JSON serialization
    prescription["_id"] = str(prescription["_id"])
    prescription["doctor_id"] = str(prescription["doctor_id"])
    prescription["patient_id"] = str(prescription["patient_id"])
    prescription["referred_appointment_id"] = str(prescription["referred_appointment_id"])

    doctor = mongo.db.doctors.find_one({"_id": ObjectId(prescription["doctor_id"])})
    if not doctor:
        return jsonify({"error": "Doctor details not found"}), 404

    # Convert ObjectId to string for JSON serialization
    doctor["_id"] = str(doctor["_id"])

    # Combine prescription and doctor details
    result = {
        "prescription": prescription,
        "doctor": {
            "name": doctor["name"],
            "specialization": doctor["specialization"],
            "contact": doctor.get("contact_number", "N/A"),  # Optional field
            "_id": doctor["_id"]
        }
    }
    # print(prescription)
    # print(result)
    # print(prescription)
    return jsonify(prescription), 200
    # return jsonify(result), 200


# @patients.route("/get_prescriptions_with_appointments/<appointment_id>", methods=["GET"])
# def get_prescriptions_with_appointments(appointment_id):
#     try:
#         # Find prescription for the given appointment ID
#         prescription = mongo.db.prescriptions.find_one({"referred_appointment_id": appointment_id})
#         if not prescription:
#             return jsonify({"error": "Prescription not found"}), 404
#
#         # Convert ObjectId to string for JSON serialization
#         prescription["_id"] = str(prescription["_id"])
#         prescription["doctor_id"] = str(prescription["doctor_id"])
#         prescription["patient_id"] = str(prescription["patient_id"])
#         prescription["referred_appointment_id"] = str(prescription["referred_appointment_id"])
#
#         # Get doctor details using the doctor_id from the prescription
#         doctor = mongo.db.doctors.find_one({"_id": ObjectId(prescription["doctor_id"])})
#         if not doctor:
#             return jsonify({"error": "Doctor details not found"}), 404
#
#         # Convert ObjectId to string for JSON serialization
#         doctor["_id"] = str(doctor["_id"])
#
#         # Combine prescription and doctor details
#         result = {
#             "prescription": prescription,
#             "doctor": {
#                 "name": doctor["name"],
#                 "specialization": doctor["specialization"],
#                 "contact": doctor.get("contact_number", "N/A"),  # Optional field
#                 "_id": doctor["_id"]
#             }
#         }
#
#         return jsonify(result), 200
#
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
