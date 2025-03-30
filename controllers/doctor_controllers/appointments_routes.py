from datetime import datetime, timedelta

from bson import ObjectId
from flask import jsonify, request, render_template, redirect

from api.doctor import doctors
from config import mongo
from middleware.auth_middleware import token_required


@doctors.route('/get-all-appointments', methods=['GET'])
@token_required
def get_all_appointments(current_user):
    # Get today's date and convert to a datetime object with the start of the day (00:00:00)
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())  # Convert to datetime

    # Get the end of the day (23:59:59) for today
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

    # Fetch today's appointments for the doctor using the doctor_id from current_user
    appointments = list(mongo.db.appointments.aggregate([
        {
            "$match": {
                "doctor_id": ObjectId(current_user),  # Ensure you're matching the doctor's ID
                "date": {
                    "$gte": start_of_day,  # Start of the day as datetime object
                    "$lt": end_of_day  # Before the next day (end of the day)
                }
            }
        },
        {
            "$lookup": {
                "from": "users",  # Join with the users collection (where patient data is stored)
                "localField": "patient_id",  # Use the patient_id from appointments
                "foreignField": "_id",  # Match it with the _id in the users collection
                "as": "patient_details"  # The resulting array will be called patient_details
            }
        },
        {
            "$unwind": "$patient_details"  # Unwind the patient_details array so we can access it directly
        },
        {
            "$project": {
                "patient_id": "$patient_details._id",
                "patient_name": "$patient_details.name",  # Get patient's name from the patient_details
                "patient_email": "$patient_details.email",  # Get patient's email from the patient_details
                "appointment_date": "$date",  # Include the appointment date
                "appointment_time": "$time",  # Include the appointment time
                "reason": "$reason",  # Include the reason for the appointment
                "status": "$status"  # Include the status of the appointment
            }
        }
    ]))

    # print(appointments)
    # If no appointments found, return an error
    if not appointments:
        return render_template('doctor/doctor_view_appointments_templates.html',
                               error="No appointments found for today")
        # return jsonify({}), 404
    #
    # for appointment in appointments:
    #     if '_id' in appointment:
    #         appointment['_id'] = str(appointment['_id'])  # Convert ObjectId to string
    #     if 'doctor_id' in appointment:
    #         appointment['doctor_id'] = str(appointment['doctor_id'])
    #     if 'patient_id' in appointment:
    #         appointment['patient_id'] = str(appointment['patient_id'])
    # Return the list of appointments

    # return jsonify({"appointments": appointments}), 200
    return render_template('doctor/doctor_view_appointments_templates.html', appointments=appointments)


@doctors.route('/get-all-booked-appointments', methods=['GET'],endpoint="get_all_booked_appointments")
@token_required
def get_all_booked_appointments(current_user):
    # Fetch today's appointments for the doctor using the doctor_id from current_user
    appointments = list(mongo.db.appointments.aggregate([
        {
            "$match": {
                "doctor_id": ObjectId(current_user),  # Ensure you're matching the doctor's ID
            }
        },
        {
            "$lookup": {
                "from": "users",  # Join with the users collection (where patient data is stored)
                "localField": "patient_id",  # Use the patient_id from appointments
                "foreignField": "_id",  # Match it with the _id in the users collection
                "as": "patient_details"  # The resulting array will be called patient_details
            }
        },
        {
            "$unwind": "$patient_details"  # Unwind the patient_details array so we can access it directly
        },
        {
            "$project": {
                "patient_id": "$patient_details._id",
                "patient_name": "$patient_details.name",  # Get patient's name from the patient_details
                "patient_email": "$patient_details.email",  # Get patient's email from the patient_details
                "appointment_date": "$date",  # Include the appointment date
                "appointment_time": "$time",  # Include the appointment time
                "reason": "$reason",  # Include the reason for the appointment
                "status": "$status"  # Include the status of the appointment
            }
        }
    ]))

    # print(appointments)
    # If no appointments found, return an error
    if not appointments:
        return render_template('doctor/doctor_view_appointments_templates.html',
                               error="No appointments found for today")
        # return jsonify({}), 404
    #
    # for appointment in appointments:
    #     if '_id' in appointment:
    #         appointment['_id'] = str(appointment['_id'])  # Convert ObjectId to string
    #     if 'doctor_id' in appointment:
    #         appointment['doctor_id'] = str(appointment['doctor_id'])
    #     if 'patient_id' in appointment:
    #         appointment['patient_id'] = str(appointment['patient_id'])
    # Return the list of appointments

    # return jsonify({"appointments": appointments}), 200
    return render_template('doctor/doctor_view_appointments_templates.html', appointments=appointments)


@doctors.route('/generate-prescriptions/<appointments_id>', methods=['GET', 'POST'])
def generate_prescription(appointments_id):
    return render_template('doctor/generate_prescriptions_templates.html', appointments_id=appointments_id)


@doctors.route('/add-generate-prescriptions/', methods=['POST'])
def add_generate_prescription():
    data = request.get_json()
    medications = data.get('medications')  # List of medications with timing and dosage
    appointment_id = data.get('appointment_id')
    notes = data.get('notes', "")
    test_reports = data.get('test_reports', [])  # List of test reports with details

    # Iterate over each test report and add additional fields (report_name, price) by fetching from lab_reports collection
    for report in test_reports:
        # Ensure report_id is in ObjectId format
        report_id = ObjectId(report['report_id']) if isinstance(ObjectId(report['report_id']), str) else ObjectId(report['report_id'])

        # Fetch the report details from the lab_reports collection
        lab_report = mongo.db.lab_reports.find_one({'_id': report_id})  # Find lab report by report_id

        if lab_report:
            # Extract the report_name and price from the lab_reports collection
            report['report_name'] = lab_report.get('report_name', '')  # Fetch report_name from lab_report
            report['price'] = lab_report.get('price', 0)  # Fetch price from lab_report
        else:
            # If lab report is not found, default to empty or zero values
            report['report_name'] = ''  # Default report_name if not found
            report['price'] = 0  # Default price if not found

        # Set the status of the report to 'pending'
        report['status_reports'] = 'pending'  # Set the status to pending

    # Prepare the prescription data
    prescription = {
        'appointment_id': ObjectId(appointment_id),
        'medications': medications,
        'test_reports': test_reports,  # Include the updated test_reports with report_name and price
        'notes': notes,
        "status": "Issued",  # Prescription status
        'created_at': datetime.utcnow(),  # Set the creation date to current UTC time
    }

    # Insert the prescription into the database
    prescription_id = mongo.db.prescriptions.insert_one(prescription).inserted_id

    # Update the status of the appointment to "Completed"
    mongo.db.appointments.update_one(
        {"_id": ObjectId(appointment_id)},  # Filter criteria
        {"$set": {"status": "Completed"}}  # Update operation
    )

    # Return success response
    return jsonify(
        {'message': "Prescription submitted successfully", 'redirect_url': "/doctor/get-all-appointments"}), 200


@doctors.route('/add-forward-appointment', methods=['POST'], endpoint='forward-appointment')
@token_required
def forward_appointment(current_user):
    try:
        # Get the data from the request body
        data = request.get_json()
        appointment_id = data['appointmentId']
        doctor_id = data['doctorId']
        new_date = data['newDate']
        new_time = data['newTime']
        new_reason = data['newReason']

        # Validate the received data
        if not all([appointment_id, doctor_id, new_date, new_time, new_reason]):
            return jsonify({"error": "All fields are required."}), 400

        # Prepare the forwarding data
        forwarding = {
            "from_doctor_id": ObjectId(current_user),  # The doctor that the appointment is forwarded from
            "to_doctor_id": ObjectId(doctor_id),  # The new doctor
            "new_date": new_date,
            "new_time": new_time,
            "new_reason": new_reason,
            "created_at": datetime.utcnow(),
        }

        # Update the appointment in the database
        result = mongo.db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$push": {"forwarding": forwarding},
                "$set": {"status": "Forwarded"}
            }
            # Push the forwarding details
        )

        if result.modified_count > 0:
            return jsonify({"message": "Appointment forwarded successfully."}), 200
        else:
            return jsonify({"error": "Appointment not found."}), 404

    except Exception as e:
        print(f"Error forwarding appointment: {e}")
        return jsonify({"error": "Internal server error"}), 500


@doctors.route('/get-forward-appointment', methods=['GET'], endpoint='get-forward-appointment')
@token_required
def get_forward_appointment(current_user):
    try:
        # Fetch the current doctor (the one who forwarded the appointment) from the 'users' collection
        current_doctor = mongo.db.users.find_one({"_id": ObjectId(current_user)})

        # If the current doctor is not found, return an error
        if not current_doctor:
            return jsonify({"error": "Current doctor not found."}), 404

        # Retrieve the forwarded appointments where current_user is the doctor that forwarded them
        forwarded_appointments = mongo.db.appointments.find({
            "forwarding.from_doctor_id": ObjectId(current_user)
        })

        # Convert cursor to list and check if it has any results
        forwarded_appointments_list = list(forwarded_appointments)

        # If no forwarded appointments are found
        if not forwarded_appointments_list:
            return render_template('doctor/forward_appointments.html', appointments=[])

        # Prepare the response data with forwarding details
        appointments_data = []
        for appointment in forwarded_appointments_list:
            # Collect relevant details including forwarding data
            forwarded_info = appointment.get('forwarding', [])

            for forward in forwarded_info:
                # Get the to_doctor_id (doctor to whom the appointment is forwarded)
                to_doctor_id = forward.get("to_doctor_id")

                # Fetch the forwarded doctor's details using their _id
                forwarded_doctor = mongo.db.users.find_one({"_id": ObjectId(to_doctor_id)})

                # If the forwarded doctor is not found, return an error
                if not forwarded_doctor:
                    return jsonify({"error": "Forwarded doctor not found."}), 404

                # Fetch the patient's details using the patient_name or user_id
                patient_id = appointment.get("patient_id")  # assuming "patient_id" holds the reference to patient in users collection
                patient_data = mongo.db.users.find_one({"_id": ObjectId(patient_id)})

                # If the patient is not found, return an error
                if not patient_data:
                    return jsonify({"error": "Patient not found."}), 404

                # Add the forwarding details to the response, including the forwarded doctor's info and patient's data
                appointment_data = {
                    "appointment_id": str(appointment['_id']),
                    "patient_name": patient_data.get("name"),
                    "patient_email": patient_data.get("email"),
                    "patient_contact": patient_data.get("mobile_number"),
                    "status": appointment.get("status"),
                    "forwarded_to_doctor": {
                        "doctor_id": str(forwarded_doctor['_id']),
                        "name": forwarded_doctor.get("name"),
                        "email": forwarded_doctor.get("email"),
                        "role": forwarded_doctor.get("role")
                    },
                    "new_date": forward.get("new_date"),
                    "new_time": forward.get("new_time"),
                    "new_reason": forward.get("new_reason"),
                    "forwarded_at": forward.get("created_at")
                }
                appointments_data.append(appointment_data)

        # Render the Jinja template and pass the data
        return render_template('doctor/forward_appointments.html', appointments=appointments_data)

    except Exception as e:
        print(f"Error retrieving forwarded appointments: {e}")
        return jsonify({"error": "Internal server error"}), 500


@doctors.route('/get-referring-appointments', methods=['GET'], endpoint='get-referring-appointments')
@token_required
def get_referring_appointments(current_user):
    try:
        # Fetch the current doctor (the one who is being referred to) from the 'users' collection
        current_doctor = mongo.db.users.find_one({"_id": ObjectId(current_user)})

        # If the current doctor is not found, return an error
        if not current_doctor:
            return jsonify({"error": "Current doctor not found."}), 404

        # Retrieve the forwarded appointments where current_user is the doctor that has been referred to
        referred_appointments = mongo.db.appointments.find({
            "forwarding.to_doctor_id": ObjectId(current_user)
        })

        # Convert cursor to list and check if it has any results
        referred_appointments_list = list(referred_appointments)

        # If no referred appointments are found, return a JSON response or a rendered template with no appointments
        if not referred_appointments_list:
            return render_template('doctor/referring_appointments.html', appointments=[])

        # Prepare the response data with forwarding details
        appointments_data = []
        patient_ids = set()
        doctor_ids = set()

        # Collect all patient_ids and doctor_ids upfront to optimize the queries
        for appointment in referred_appointments_list:
            forwarded_info = appointment.get('forwarding', [])
            for forward in forwarded_info:
                doctor_ids.add(forward.get("to_doctor_id"))
                patient_ids.add(appointment.get("patient_id"))

        # Query for referred doctors and patients all at once (optimization)
        referred_doctors = mongo.db.users.find({"_id": {"$in": list(doctor_ids)}})
        referred_doctors_dict = {str(doctor['_id']): doctor for doctor in referred_doctors}

        patients = mongo.db.users.find({"_id": {"$in": list(patient_ids)}})
        patients_dict = {str(patient['_id']): patient for patient in patients}

        # Loop through appointments to build the response data
        for appointment in referred_appointments_list:
            forwarded_info = appointment.get('forwarding', [])
            for forward in forwarded_info:
                to_doctor_id = forward.get("to_doctor_id")
                referred_doctor = referred_doctors_dict.get(str(to_doctor_id))
                patient_id = appointment.get("patient_id")
                patient_data = patients_dict.get(str(patient_id))

                # If the referred doctor or patient is not found, skip this appointment
                if not referred_doctor or not patient_data:
                    continue

                # Add the referral details to the response
                appointment_data = {
                    "appointment_id": str(appointment['_id']),
                    "patient_name": patient_data.get("name"),
                    "patient_email": patient_data.get("email"),
                    "patient_contact": patient_data.get("mobile_number"),
                    "status": appointment.get("status"),
                    "referred_to_doctor": {
                        "doctor_id": str(referred_doctor['_id']),
                        "name": referred_doctor.get("name"),
                        "email": referred_doctor.get("email"),
                        "role": referred_doctor.get("role")
                    },
                    "new_date": forward.get("new_date"),
                    "new_time": forward.get("new_time"),
                    "new_reason": forward.get("new_reason"),
                    "referred_at": forward.get("created_at")
                }
                appointments_data.append(appointment_data)

        # If we have no data to return, render the template with an empty list
        if not appointments_data:
            return render_template('doctor/referring_appointments.html', appointments=[])

        print(appointments_data)
        # Pass the populated appointments data to the template
        return render_template('doctor/referring_appointments.html', appointments=appointments_data)

    except Exception as e:
        # Log error for debugging purposes
        return jsonify({"error": "Internal Server Error"}), 500


@doctors.route('/close-appointment/<appointment_id>', methods=['GET'],endpoint='close_appointment')
def cancel_appointment(appointment_id):

    if not all([appointment_id]):
        return jsonify({"error": "All fields are required"}), 400

    mongo.db.appointments.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": "close"}}
    )

    return redirect('/doctor/get-all-booked-appointments')
