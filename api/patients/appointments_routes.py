import uuid

from bson import ObjectId
from flask import jsonify

from api.patients import patients
from flask import request, jsonify

from config import mongo


@patients.route('/book-appointment', methods=['POST'])
def book_appointment():
    data = request.json
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    date = data.get('date')
    time = data.get('time')
    reason = data.get('reason')

    # Check if the doctor is already booked at the same time
    patients = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    if not patients:
        return jsonify({"error": "patients not found"}), 404


    if not all([patient_id, doctor_id, date, time, reason]):
        return jsonify({"error": "All fields are required"}), 400

    # Check if the doctor is already booked at the same time
    doctor = mongo.db.doctors.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    overlapping_appointment = any(
        appt for appt in doctor.get('appointments', [])
        if appt['date'] == date and appt['time'] == time and appt['status'] == "Scheduled"
    )
    if overlapping_appointment:
        return jsonify({"error": "Doctor is already booked for this time"}), 400

    # Create a new appointment
    appointment_id = str(uuid.uuid4())
    new_appointment = {
        "appointment_id": appointment_id,
        "date": date,
        "time": time,
        "doctor": ObjectId(doctor_id),
        "reason": reason,
        "status": "Scheduled"
    }

    # Update patient and doctor records
    mongo.db.patients.update_one(
        {"_id": ObjectId(patient_id)},
        {"$push": {"appointments": new_appointment}}
    )

    mongo.db.doctors.update_one(
        {"_id": ObjectId(doctor_id)},
        {"$push": {"appointments": {
            "appointment_id": appointment_id,
            "patient_id": ObjectId(patient_id),
            "date": date,
            "time": time,
            "reason": reason,
            "status": "Scheduled"
        }}}
    )

    return jsonify({"message": "Appointment booked successfully", "appointment_id": appointment_id}), 200


@patients.route('/view-appointments/<patient_id>', methods=['GET'])
def view_appointments(patient_id):
    patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    return jsonify({"appointments": patient.get('appointments', [])}), 200


@patients.route('/cancel-appointment', methods=['POST'])
def cancel_appointment():
    data = request.json
    patient_id = data.get('patient_id')
    appointment_id = data.get('appointment_id')

    if not all([patient_id, appointment_id]):
        return jsonify({"error": "All fields are required"}), 400

    # Update the appointment status in both patient and doctor records
    mongo.db.patients.update_one(
        {"_id": ObjectId(patient_id), "appointments.appointment_id": appointment_id},
        {"$set": {"appointments.$.status": "Cancelled"}}
    )

    mongo.db.doctors.update_one(
        {"appointments.appointment_id": appointment_id},
        {"$set": {"appointments.$.status": "Cancelled"}}
    )

    return jsonify({"message": "Appointment cancelled successfully"}), 200
