from bson import ObjectId
from flask import jsonify, request

from api.patients import patients
from config import mongo


@patients.route('/add-visitor', methods=['POST'])
def add_visitor():
    data = request.get_json()
    patient_id = data.get('patient_id')  # Patient's unique ID
    visitor_name = data.get('name')
    relationship = data.get('relationship')
    contact = data.get('contact')

    if not all([patient_id, visitor_name, relationship, contact]):
        return jsonify({"error": "All fields are required"}), 400

    # Find the patient
    patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    # Check visitor limit
    if len(patient.get('visitors', [])) >= 2:
        return jsonify({"error": "Visitor limit reached"}), 400

    # Add visitor
    new_visitor = {"name": visitor_name, "relationship": relationship, "contact": contact}
    mongo.db.patients.update_one({"_id": ObjectId(patient_id)}, {"$push": {"visitors": new_visitor}})

    return jsonify({"message": "Visitor added successfully"}), 200


@patients.route('/get-visitors/<patient_id>', methods=['GET'])
def get_visitors(patient_id):
    patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    return jsonify({"visitors": patient.get('visitors', [])}), 200


@patients.route('/remove-visitor', methods=['POST'])
def remove_visitor():
    data = request.json
    patient_id = data.get('patient_id')
    visitor_name = data.get('name')

    if not all([patient_id, visitor_name]):
        return jsonify({"error": "All fields are required"}), 400

    # Find the patient
    patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    # Remove the visitor
    mongo.db.patients.update_one({"_id": ObjectId(patient_id)}, {"$pull": {"visitors": {"name": visitor_name}}})

    return jsonify({"message": "Visitor removed successfully"}), 200
