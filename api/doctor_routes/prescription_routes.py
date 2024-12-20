from datetime import datetime

from bson import ObjectId
from flask import jsonify,request

from api.doctor_routes import doctors
from config import mongo


@doctors.route('/prescriptions', methods=['POST'])
def generate_prescription():
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    patient_id = data.get('patient_id')
    medications = data.get('medications')  # List of medications with timing and dosage
    referred_appointment_id = data.get('referred_appointment_id')
    notes = data.get('notes', "")
    test_reports = data.get('test_report', [])  # List of test reports with details

    if not all([doctor_id, patient_id, medications]):
        return jsonify({"error": "Doctor ID, Patient ID, and Medications are required"}), 400

    # Verify the referred appointment exists
    referred_appointment = mongo.db.patients.find_one(
        {"appointments.appointment_id": referred_appointment_id, "_id": ObjectId(patient_id)}
    )
    if not referred_appointment:
        return jsonify({"error": "Referred appointment not found for this patient"}), 404

    # Create prescription document
    prescription = {
        "doctor_id": ObjectId(doctor_id),
        "patient_id": ObjectId(patient_id),
        "referred_appointment_id": referred_appointment_id,
        "medications": medications,  # List of medications with timing and dosage
        "test_report": [
            {
                "report_name": report.get('report_name'),
                "result_time": report.get('result_time'),
                "additional_details": report.get('additional_details', ""),
                "status": report.get('status', "Pending"),
                "notes": report.get('notes', "")
            } for report in test_reports
        ],
        "notes": notes,
        "date": datetime.utcnow(),
        "status": "Issued"
    }

    # Insert prescription into database
    prescription_id = mongo.db.prescriptions.insert_one(prescription).inserted_id

    # Send prescription to patient and pharmacy (for demonstration, print notifications)
    patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    if patient:
        # Logic for sending notification/email to patient
        print(f"Prescription sent to patient {patient['name']}.")

    # Send to pharmacy (you can modify this to integrate with an actual pharmacy API)
    pharmacy = mongo.db.pharmacies.find_one({"name": "Main Pharmacy"})  # Example pharmacy name
    if pharmacy:
        # Logic for sending prescription to pharmacy
        print(f"Prescription sent to pharmacy {pharmacy['name']}.")

    return jsonify(
        {"message": "Prescription generated and sent successfully", "prescription_id": str(prescription_id)}), 201
