from datetime import datetime

from flask import jsonify

from api.doctor_routes import doctors
from config import mongo


@doctors.route("/generate_prescription", methods=["POST"])
def generate_prescription():
    data = request.json
    patient_id = data.get("patient_id")
    doctor_id = data.get("doctor_id")
    medications = data.get("medications")
    pharmacy_id = data.get("pharmacy_id")
    notes = data.get("notes")

    if not patient_id or not doctor_id or not medications or not pharmacy_id:
        return jsonify({"error": "Patient, doctor, medications, and pharmacy are required"}), 400

    # Generate prescription data
    prescription_data = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "medications": medications,
        "date_issued": datetime.utcnow(),
        "pharmacy_id": pharmacy_id,
        "notes": notes,
        "checkups": []  # Initially no check-ups, will be added later
    }

    # Save to MongoDB
    result = mongo.db.prescriptions.insert_one(prescription_data)

    # Return response with prescription data (including generated _id)
    prescription_data["_id"] = str(result.inserted_id)
    return jsonify(prescription_data), 200
