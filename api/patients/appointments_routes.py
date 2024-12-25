import uuid
from datetime import datetime

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
    try:
        # Fetch the patient by their ObjectId
        patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Process appointments to ensure ObjectId fields are converted to strings
        appointments = patient.get('appointments', [])
        for appointment in appointments:
            if "doctor" in appointment and isinstance(appointment["doctor"], ObjectId):
                appointment["doctor"] = str(appointment["doctor"])

        # Return the JSON response
        return jsonify({"appointments": appointments}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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


@patients.route('/feedback/submit', methods=['POST'])
def submit_patient_feedback():
    data = request.get_json()
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    appointment_id = data.get('appointment_id')
    survey_responses = data.get('survey_responses')  # Dict of responses like doctor_communication, etc.

    # Validate required fields
    if not all([patient_id, doctor_id, appointment_id, survey_responses]):
        return jsonify({"error": "Patient ID, Doctor ID, Appointment ID, and Survey Responses are required"}), 400

    # Create feedback document
    feedback = {
        "patient_id": ObjectId(patient_id),
        "doctor_id": ObjectId(doctor_id),
        "appointment_id": appointment_id,
        "survey_responses": survey_responses,
        "feedback_timestamp": datetime.utcnow()
    }

    # Insert feedback into the database
    mongo.db.patient_feedback.insert_one(feedback)

    # Update doctor performance
    update_doctor_performance(doctor_id, survey_responses)

    return jsonify({"message": "Feedback submitted successfully"}), 201

def update_doctor_performance(doctor_id, survey_responses):
    # Retrieve current doctor performance data
    performance_data = mongo.db.doctor_performance.find_one({"doctor_id": ObjectId(doctor_id)})

    if performance_data:
        updated_performance = {}
        for key, value in survey_responses.items():
            # Adjust existing rating based on the feedback count
            current_avg = performance_data['average_ratings'].get(key, 0)
            current_count = performance_data['feedback_count']
            new_avg = ((current_avg * current_count) + value) / (current_count + 1)
            updated_performance[key] = new_avg

        # Update doctor performance
        mongo.db.doctor_performance.update_one(
            {"doctor_id": ObjectId(doctor_id)},
            {"$set": {
                "average_ratings": updated_performance,
                "feedback_count": performance_data['feedback_count'] + 1
            }}
        )
    else:
        # Create initial performance data if none exists
        new_performance = {
            "doctor_id": ObjectId(doctor_id),
            "average_ratings": survey_responses,
            "feedback_count": 1
        }
        mongo.db.doctor_performance.insert_one(new_performance)

@patients.route('/feedback/appointment', methods=['GET'])
def get_appointment_feedback():
    appointment_id = request.args.get('appointment_id')

    if not appointment_id:
        return jsonify({"error": "Appointment ID is required"}), 400

    feedback_data = mongo.db.patient_feedback.find_one({"appointment_id": appointment_id})

    if not feedback_data:
        return jsonify({"error": "No feedback found for this appointment"}), 404

    return jsonify(str(feedback_data)), 200


@patients.route('/feedback/doctor-performance', methods=['GET'])
def get_doctor_performance():
    doctor_id = request.args.get('doctor_id')

    if not doctor_id:
        return jsonify({"error": "Doctor ID is required"}), 400

    performance_data = mongo.db.doctor_performance.find_one({"doctor_id": ObjectId(doctor_id)})

    if not performance_data:
        return jsonify({"error": "No performance data found for this doctor"}), 404

    return jsonify(str(performance_data)), 200
