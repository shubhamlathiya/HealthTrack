from bson import ObjectId
from flask import jsonify ,request

from api.doctor_routes import doctors
from config import mongo


@doctors.route('/get-all-appointments/<doctor_id>', methods=['GET'])
def get_all_appointments(doctor_id):
    # Find the doctor by ID
    doctor = mongo.db.doctors.find_one({"_id": ObjectId(doctor_id)})

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    # Get all the appointments associated with the doctor
    all_appointments = doctor.get('appointments', [])

    # Convert ObjectId to string in all appointments
    for appointment in all_appointments:
        # appointment['_id'] = str(appointment['_id'])  # Convert ObjectId to string
        if 'doctor_id' in appointment:
            appointment['doctor_id'] = str(appointment['doctor_id'])
        if 'patient_id' in appointment:
            appointment['patient_id'] = str(appointment['patient_id'])

    # Return the list of all appointments
    return jsonify({"all_appointments": all_appointments}), 200


@doctors.route('/forward-appointment', methods=['POST'])
def forward_appointment():
    data = request.get_json()
    appointment_id = data.get('appointment_id')
    referring_doctor_id = data.get('referring_doctor_id')
    referred_doctor_id = data.get('referred_doctor_id')
    new_date = data.get('new_date')
    new_time = data.get('new_time')

    if not all([appointment_id, referring_doctor_id, referred_doctor_id, new_date, new_time]):
        return jsonify({"error": "All fields are required"}), 400

    # Get the referring doctor and appointment details
    referring_doctor = mongo.db.doctors.find_one({"_id": ObjectId(referring_doctor_id)})
    if not referring_doctor:
        return jsonify({"error": "Referring doctor not found"}), 404

    appointment = next((appt for appt in referring_doctor.get('appointments', []) if appt['appointment_id'] == appointment_id), None)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    # Get the referred doctor details
    referred_doctor = mongo.db.doctors.find_one({"_id": ObjectId(referred_doctor_id)})
    if not referred_doctor:
        return jsonify({"error": "Referred doctor not found"}), 404

    # Update the appointment in referring doctor's record
    mongo.db.doctors.update_one(
        {"_id": ObjectId(referring_doctor_id), "appointments.appointment_id": appointment_id},
        {"$set": {
            "appointments.$.status": "Referred",
            "appointments.$.referred_to": {
                "doctor_id": ObjectId(referred_doctor['_id']),
                "name": referred_doctor['name'],
                "specialization": referred_doctor['specialization'],
                "new_date": new_date,
                "new_time": new_time
            }
        }}
    )

    # Add the appointment to the referred doctor's record
    new_appointment = {
        "appointment_id": appointment_id,
        "patient_id": appointment['patient_id'],
        "date": new_date,
        "time": new_time,
        "reason": appointment['reason'],
        "status": "Scheduled",
        "referring_doctor": {
            "doctor_id": ObjectId(referring_doctor['_id']),
            "name": referring_doctor['name'],
            "specialization": referring_doctor['specialization']
        }
    }

    mongo.db.doctors.update_one(
        {"_id": ObjectId(referred_doctor_id)},
        {"$push": {"appointments": new_appointment}}
    )

    # Update the patient's record with the new appointment
    mongo.db.patients.update_one(
        {"_id": ObjectId(appointment['patient_id'])},
        {"$push": {"appointments": {
            "appointment_id": appointment_id,
            "doctor": referred_doctor['name'],
            "date": new_date,
            "time": new_time,
            "reason": appointment['reason'],
            "status": "Scheduled"
        }}}
    )

    # Notify the patient
    patient = mongo.db.patients.find_one({"_id": ObjectId(appointment['patient_id'])})
    if patient:
        # Logic for sending email/notification to patient
        print(f"Notification sent to patient {patient['name']} about new appointment.")

    return jsonify({"message": "Appointment forwarded successfully"}), 200


@doctors.route('/get-forwarded-appointments/<doctor_id>', methods=['GET'])
def get_forwarded_appointments(doctor_id):
    doctor = mongo.db.doctors.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    referred_appointments = [
        appt for appt in doctor.get('appointments', [])
        if appt.get('status') == "Referred"
    ]

    return jsonify({"referred_appointments": str(referred_appointments)}), 200


@doctors.route('/get-referring-appointments/<doctor_id>', methods=['GET'])
def get_referring_appointments(doctor_id):
    # Find the doctor by ID
    doctor = mongo.db.doctors.find_one({"_id": ObjectId(doctor_id)})

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    # Filter appointments with status 'Referred' from the referring doctor
    referring_appointments = [
        appt for appt in doctor.get('appointments', [])
        if appt.get('status') == "Scheduled" and 'referred_to' not in appt
    ]

    # Return the list of referring appointments
    return jsonify({"referring_appointments": str(referring_appointments)}), 200
