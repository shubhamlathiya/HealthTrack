import uuid
from datetime import datetime

from bson import ObjectId
from flask import jsonify, render_template

from controllers.patients_controllers import patients
from flask import request, jsonify

from utils.config import mongo
from middleware.auth_middleware import token_required


@patients.route('/book-Appointment', methods=['GET', 'POST'],endpoint='bookAppointment')
@token_required
def book_appointment(current_user):
    if request.method == 'GET':
        pipeline = [
            {
                "$match": {
                    "role": "doctor"  # Ensure that only doctors are fetched from the users collection
                }
            },
            {
                "$lookup": {
                    "from": "DoctorsAndStaff",  # The collection to join with
                    "localField": "_id",  # Field in the users collection to match with
                    "foreignField": "user_id",  # Field in the DoctorsAndStaff collection to match with
                    "as": "doctor_details"  # The alias for the joined data
                }
            },
            {
                "$unwind": "$doctor_details"  # Flatten the joined data
            },
            {
                "$project": {
                    "name": 1,
                    "specialization": "$doctor_details.specialization",  # Extract specialization from the joined data
                }
            }
        ]

        # Execute the aggregation query
        doctors = list(mongo.db.users.aggregate(pipeline))
        # print(doctors)
        # return jsonify(doctor_data)
        return render_template('patient_templates/patient_book_appointment_templates.html', doctors=doctors,
                               patientId=current_user)
    elif request.method == 'POST':
        data = request.get_json()
        doctor_id = ObjectId(data['doctorId'])
        patient_id = ObjectId(data['patient_id'])
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d')
        appointment_time = data['time']
        reason = data['reason']

        # print(data)
        patients = mongo.db.users.find_one({"_id": ObjectId(patient_id)})
        if not patients:
            return jsonify({"error": "patients not found"}), 404

        if not all([patient_id, doctor_id, appointment_date, appointment_time, reason]):
            return jsonify({"error": "All fields are required"}), 400

        existing_appointment = mongo.db.appointments.find_one({
            "doctor_id": doctor_id,
            "date": appointment_date,
            "time": appointment_time
        })

        if existing_appointment:
            # Doctor is already booked at this time
            return jsonify({"error": "The doctor is already booked at this time. Please choose another time."}), 400

        # doctor = mongo.db.users.find_one({"_id": ObjectId(doctor_id)})
        # if not doctor:
        #     return jsonify({"error": "Doctor not found"}), 404
        appointment_data = {
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "date": appointment_date,
            "time": appointment_time,
            "reason": reason,
            "status": "Scheduled",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Insert the new appointment into the database
        result = mongo.db.appointments.insert_one(appointment_data)

        if result.inserted_id:
            return jsonify({"message": "Appointment booked successfully!"}), 201
        else:
            return jsonify({"error": "Failed to book appointment"}), 500


@patients.route('/get-appointments', methods=['GET'] , endpoint='get_appointments')
@token_required
def get_appointments_for_patient(current_user):
    # Aggregation pipeline to fetch appointments along with doctor details
    pipeline = [
        {
            "$match": {
                "patient_id": ObjectId(current_user)  # Filter appointments by current user's patient_id
            }
        },
        {
            "$lookup": {
                "from": "DoctorsAndStaff",  # Join with the DoctorsAndStaff collection
                "localField": "doctor_id",  # Use the doctor_id from appointments
                "foreignField": "user_id",  # Match it with the user_id in DoctorsAndStaff
                "as": "doctor_details"  # This will contain the doctor details in an array
            }
        },
        {
            "$unwind": "$doctor_details"  # Unwind the doctor_details array so we can access it directly
        },
        {
            "$lookup": {
                "from": "users",  # Join with the DoctorsAndStaff collection
                "localField": "doctor_id",  # Use the doctor_id from appointments
                "foreignField": "_id",  # Match it with the user_id in DoctorsAndStaff
                "as": "users_details"  # This will contain the doctor details in an array
            }
        },
        {
            "$unwind": "$users_details"  # Unwind the doctor_details array so we can access it directly
        },
        {
            "$project": {
                "appointment_id": "$_id",  # Include the appointment ID
                "doctor_id": "$users_details._id",
                "doctor_name": "$users_details.name",  # Get doctor name from doctor_details
                "specialization": "$doctor_details.specialization",  # Get doctor specialization
                "appointment_date": "$date",  # Include the appointment date
                "appointment_time": "$time",  # Include the appointment time
                "reason": "$reason",  # Include the reason for the appointment
                "status": "$status"  # Include the status of the appointment
            }
        }
    ]

    # Execute the aggregation pipeline
    appointments = list(mongo.db.appointments.aggregate(pipeline))

    # print(appointments)
    # If no appointments found, return an error message
    if not appointments:
        return render_template("patient_templates/patient_view_appointment_templates.html" , error = "No appointments found for this patient")
        # return jsonify({"error": "No appointments found for this patient"}), 404

    # Render the template with appointments and doctor details
    return render_template('patient_templates/patient_view_appointment_templates.html', appointments=appointments,
                           patientId=current_user)

@patients.route('/cancel-appointment', methods=['POST'],endpoint='cancel_appointment')
def cancel_appointment():
    data = request.json

    appointment_id = data.get('appointment_id')

    if not all([appointment_id]):
        return jsonify({"error": "All fields are required"}), 400


    mongo.db.appointments.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": "Cancelled"}}
    )

    return jsonify({"message": "Appointment cancelled successfully"}), 200


# @patients.route('/appointments' ,methods=['GET'],endpoint='appointments1')
# def get_appointments():
#     return render_template('patient/patient_view_appointment_templates.html')
