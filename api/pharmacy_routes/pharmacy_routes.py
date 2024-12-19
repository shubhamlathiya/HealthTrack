from bson import ObjectId
from flask import jsonify

from api.pharmacy_routes import pharmacy
from config import mongo


@pharmacy.route('/prescriptions/<patient_id>', methods=['GET'])
def get_prescriptions(patient_id):
    # Fetch prescriptions for the given patient ID
    prescriptions = mongo.db.prescriptions.find({"patient_id": ObjectId(patient_id)})

    if not prescriptions:
        return jsonify({"error": "No prescriptions found for this patient"}), 404

    prescription_list = [{"medication": p['medication'], "dosage": p['dosage'], "date": p['date']} for p in
                         prescriptions]

    return jsonify({"prescriptions": prescription_list}), 200


@pharmacy.route('/patient-history/<patient_id>', methods=['GET'])
def get_patient_history(patient_id):
    # Fetch all prescriptions for the given patient ID
    prescriptions = mongo.db.prescriptions.find({"patient_id": ObjectId(patient_id)})

    if not prescriptions:
        return jsonify({"error": "No medication history found for this patient"}), 404

    medication_history = [{"medication": p['medication'], "dosage": p['dosage'], "date": p['date']} for p in
                          prescriptions]

    return jsonify({"medication_history": medication_history}), 200
