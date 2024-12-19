from bson import ObjectId
from flask import jsonify

from api.patients import patients
from config import mongo


@patients.route('/medical-records/<patient_id>', methods=['GET'])
def get_medical_records(patient_id):
    # Find the patient
    patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    # Return medical records
    medical_records = patient.get('medical_records', [])
    return jsonify({"medical_records": medical_records}), 200
