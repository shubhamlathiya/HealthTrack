from bson import ObjectId
from flask import jsonify

from api.patients import patients
from config import mongo


@patients.route("/get_prescription/<prescription_id>", methods=["GET"])
def get_prescription(prescription_id):
    prescription = mongo.db.prescriptions.find_one({"_id": ObjectId(prescription_id)})
    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    # Convert ObjectId to string for JSON serialization
    prescription["_id"] = str(prescription["_id"])

    return jsonify(prescription), 200
