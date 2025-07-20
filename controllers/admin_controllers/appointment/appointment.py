from datetime import timedelta

from flask import render_template, request, jsonify, redirect, flash
from sqlalchemy.orm import joinedload

from controllers.admin_controllers import admin
from models.appointmentModel import Appointment, AppointmentTreatment
from models.departmentAssignmentModel import DepartmentAssignment
from models.departmentModel import Department
from models.doctorModel import Doctor, Availability
from models.patientModel import Patient
from models.treatmentModel import Treatment
from models.userModel import User
from utils.config import db
from utils.create_new_patient import create_new_patient
from utils.generate_time_slots import generate_time_slots


@admin.route("/appointments", methods=["GET"], endpoint="appointment")
def list_appointments():
    try:
    # Fetch all appointments with their related data
        appointments = db.session.query(Appointment) \
            .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor),
            joinedload(Appointment.original_doctor),
            joinedload(Appointment.treatments).joinedload(AppointmentTreatment.treatment)
        ) \
            .all()
        # Sort appointments by date and start time
        appointments.sort(key=lambda a: (a.date, a.start_time))

        return render_template('admin_templates/appointment/appointments.html',
                               appointments=appointments,
                               datetime=datetime)
    except Exception as e:
        flash(f"Error fetching appointments: {str(e)}", "danger")
        return redirect("/admin/appointments")


# except Excepti
@admin.route("/appointments/book-appointment", methods=['GET'], endpoint='book-appointment')
def appointment():
    # Get all active departments
    departments = Department.query.filter_by(is_deleted=False).all()

    # Get all active treatments
    treatments = Treatment.query.filter_by(active=True, is_deleted=False).all()

    # Get all active doctors
    doctors = Doctor.query.filter_by(is_deleted=False).all()

    return render_template(
        'admin_templates/appointment/book-appointment.html',
        departments=departments,
        treatments=treatments,
        doctors=doctors
    )


@admin.route('/book-appointment', methods=['POST'])
def book_appointment():
    # Handle POST request for form submission
    data = request.form
    print(data)
    # Check if this is an existing patient
    if data.get('patient_id'):
        # Existing patient path
        patient = Patient.query.filter_by(patient_id=data['patient_id']).first()
        if not patient:
            flash('Patient not found with the provided ID', 'danger')
            return redirect(request.url)
    else:
        # Check if user email exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            flash('Email already exists in the system', 'danger')
            return redirect(request.url)

            # Create new patient using the function
        patient = create_new_patient({
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'email': data['email'],
            'phone': data['phone'],
            'age': data.get('age'),
            'gender': data.get('gender')
        })
    # Create appointment (for both new and existing patients)
    appointment = Appointment(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        start_time=datetime.strptime(data['time'], '%H:%M').time(),
        end_time=(datetime.strptime(data['time'], '%H:%M') + timedelta(minutes=30)).time(),
        reason=data['reason'],
        patient_id=patient.id,
        doctor_id=data['doctor_id']
    )
    db.session.add(appointment)
    db.session.commit()

    return redirect("/admin/appointment-success" + appointment.id)


@admin.route('/get-doctors/<int:department_id>')
def get_doctors(department_id):
    doctors = Doctor.query \
        .join(DepartmentAssignment) \
        .filter(DepartmentAssignment.department_id == department_id) \
        .all()

    doctors_data = [{
        'id': d.id,
        'name': f"{d.first_name} {d.last_name}",
        'specialties': [da.specialty for da in d.department_assignments]
    } for d in doctors]

    return jsonify(doctors_data)


from datetime import datetime


@admin.route('/get-available-slots/<int:doctor_id>/<date>')
def get_available_slots(doctor_id, date):
    try:
        # Parse the date from the URL to a datetime object
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        # Get the day of the week (e.g., 'Monday', 'Tuesday', etc.)
        day_of_week_name = appointment_date.strftime('%A')

        # Map the day name to the corresponding number (1 for Monday, 7 for Sunday)
        days_map = {
            'Monday': 1,
            'Tuesday': 2,
            'Wednesday': 3,
            'Thursday': 4,
            'Friday': 5,
            'Saturday': 6,
            'Sunday': 7
        }

        day_of_week = days_map.get(day_of_week_name)

        # Debug log: print out the values to check if everything is correct
        print(
            f"Looking for availability for doctor {doctor_id} on {day_of_week_name} (Day {day_of_week}) for date {appointment_date}")

        # Get doctor's availability for this day (now using day_of_week number)
        availability = Availability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_of_week
        ).first()
        print(availability)
        # If no availability found, return an error message
        if not availability:
            print(f"No availability found for doctor {doctor_id} on {day_of_week_name}")
            return jsonify({'error': 'Doctor not available on this day'}), 400

        # Get existing appointments for this doctor on this date
        existing_appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=appointment_date
        ).all()

        # Generate time slots based on the availability and existing appointments
        slots = generate_time_slots(
            availability.from_time,
            availability.to_time,
            existing_appointments
        )

        # Return the available slots
        return jsonify({'slots': slots})

    except Exception as e:
        # In case of any exception, return an error message with the exception
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin.route('/appointment-success/<int:appointment_id>')
def appointment_success(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('admin_templates/appointment/appointment-success.html', appointment=appointment)
