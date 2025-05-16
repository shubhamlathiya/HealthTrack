from datetime import datetime, timedelta, date

from flask import render_template, request, jsonify, flash, redirect
from sqlalchemy import and_, or_, not_

from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models.appointmentModel import Appointment, AppointmentTreatment
from models.departmentModel import Department
from models.doctorModel import Doctor
from models.patientModel import Patient
from models.treatmentModel import Treatment
from models.userModel import User, UserRole
from utils.config import db
from utils.email_utils import send_email


@patients.route('/appointment', methods=['GET'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def appointment(current_user):
    patients = Patient.query.filter_by(user_id=current_user).first()

    appointments = Appointment.query.filter_by(
        patient_id=patients.id
    ).order_by(
        Appointment.date.desc()
    ).all()

    return render_template("patient_templates/appointment/list_appointments.html",
                           appointments=appointments,
                           patient=patients,
                           date=date
                           )


@patients.route('/book-appointment', methods=['GET'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def book_appointment(current_user):
    # Get all active departments
    departments = Department.query.filter_by(is_deleted=False).all()

    # Get all active treatments
    treatments = Treatment.query.filter_by(active=True, is_deleted=False).all()

    patients = Patient.query.filter_by(user_id=current_user).first()
    # Get patient's recent appointments
    recent_appointments = Appointment.query.filter_by(
        patient_id=patients.id
    ).order_by(
        Appointment.date.desc()
    ).limit(3).all()

    return render_template(
        'patient_templates/appointment/book_appointment.html',
        departments=departments,
        treatments=treatments,
        recent_appointments=recent_appointments,
        current_user=patients
    )


@patients.route('/book-appointment', methods=['POST'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def create_appointment(current_user):
    try:
        data = request.get_json()  # Changed from request.form to request.get_json()
        print(data)
        # Validate required fields
        required_fields = ['doctor_id', 'date', 'start_time', 'reason']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Get patient record
        patient = Patient.query.filter_by(user_id=current_user).first()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        # Parse date and times
        try:
            appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = (datetime.strptime(data['start_time'], '%H:%M') + timedelta(minutes=30)).time()

        except ValueError as e:
            return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400

        # Create appointment
        appointment = Appointment(
            date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            patient_id=patient.id,
            doctor_id=data['doctor_id'],
            reason=data['reason'],
            status='scheduled',
            created_at=datetime.utcnow()
        )

        # Handle forwarded appointments if applicable
        if 'original_doctor_id' in data:
            appointment.original_doctor_id = data['original_doctor_id']

        db.session.add(appointment)
        db.session.flush()  # To get the appointment ID

        # Add selected treatments
        for treatment_id in data['treatment_ids']:
            treatment = Treatment.query.get(treatment_id)
            if not treatment:
                db.session.rollback()
                return jsonify({'error': f'Treatment with ID {treatment_id} not found'}), 404

            appointment_treatment = AppointmentTreatment(
                appointment_id=appointment.id,
                treatment_id=treatment.id,
                price=treatment.base_price,
                status='pending'
            )
            db.session.add(appointment_treatment)

        db.session.commit()

        # Get doctor's details
        doctor = Doctor.query.get(data['doctor_id'])
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404

        # Prepare response
        response = {
            'message': 'Appointment booked successfully'
        }

        users = User.query.filter_by(id=current_user).first()
        body_html = render_template("email_templates/templates/appointment_mail.html",
                                    appointment=appointment,
                                    patient=patient,
                                    appointment_link="/")
        subject = f"Appointment Confirmation - {appointment.date}"
        send_email(subject, users.email, body_html)

        return jsonify(response), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@patients.route('/patient/appointments/reschedule/<int:appointment_id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def reschedule_appointment(current_user, appointment_id):
    try:
        # Get the original appointment
        original_appointment = Appointment.query.get_or_404(appointment_id)
        patient = Patient.query.filter_by(user_id=current_user.id).first()

        # Verify ownership
        if not patient or original_appointment.patient_id != patient.id:
            flash('Unauthorized access to appointment', 'error')
            return redirect("/patient/appointment")

        # Only allow rescheduling of scheduled appointments
        if original_appointment.status != 'scheduled':
            flash('Only scheduled appointments can be rescheduled', 'error')
            return redirect("/patient/appointment")

        # Get form data
        new_date_str = request.form.get('date')
        time_slot_str = request.form.get('time_slot')
        reason = request.form.get('reason', original_appointment.reason)

        # Validate inputs
        if not new_date_str or not time_slot_str:
            flash('Please select both date and time slot', 'error')
            return redirect("/patient/appointment")

        try:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(time_slot_str, '%H:%M:%S').time()
        except ValueError:
            flash('Invalid date or time format', 'error')
            return redirect("/patient/appointment")

        # Calculate end time (assuming 30-minute slots)
        end_time = (datetime.combine(date.min, start_time) + timedelta(minutes=30)).time()

        # Check if the new slot is available
        conflicting_appointment = Appointment.query.filter(
            and_(
                Appointment.doctor_id == original_appointment.doctor_id,
                Appointment.date == new_date,
                or_(
                    and_(
                        Appointment.start_time <= start_time,
                        Appointment.end_time > start_time
                    ),
                    and_(
                        Appointment.start_time < end_time,
                        Appointment.end_time >= end_time
                    ),
                    and_(
                        Appointment.start_time >= start_time,
                        Appointment.end_time <= end_time
                    )
                ),
                Appointment.status == 'scheduled',
                not_(Appointment.id == appointment_id)
            )
        ).first()

        if conflicting_appointment:
            flash('The selected time slot is no longer available', 'error')
            return redirect("/patient/appointment")

        # Update the appointment
        original_appointment.date = new_date
        original_appointment.start_time = start_time
        original_appointment.end_time = end_time
        original_appointment.reason = reason
        original_appointment.status = 'rescheduled'
        original_appointment.rescheduled_at = datetime.utcnow()

        db.session.commit()
        #
        # # Send confirmation email
        # send_reschedule_confirmation(current_user, original_appointment)

        flash('Appointment successfully rescheduled', 'success')
        return redirect("/patient/appointment")

    except Exception as e:
        db.session.rollback()
        flash('An error occurred while rescheduling your appointment', 'error')
        return redirect("/patient/appointment")


@patients.route('/appointments/cancel/<int:appointment_id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def cancel_appointment(current_user, appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    user = User.query.filter_by(id=current_user).first()
    patient = Patient.query.filter_by(user_id=current_user).first()

    if appointment.patient_id != patient.id:
        flash('Unauthorized to cancel this appointment.', 'danger')
        return redirect("/patient/appointment")

    if appointment.status != 'scheduled':
        flash('Only scheduled appointments can be canceled.', 'warning')
        return redirect("/patient/appointment")

    appointment.status = 'canceled'
    appointment.canceled_at = datetime.utcnow()
    db.session.commit()

    # Send cancellation email
    body_html = render_template("email_templates/templates/appointment_canceled_mail.html",
                                appointment=appointment,
                                patient=patient,
                                booking_link="/")
    subject = f"Appointment Cancellation Confirmation - {appointment.date}"
    send_email(subject, user.email, body_html)

    flash('Your appointment has been successfully canceled.', 'success')
    return redirect("/patient/appointment")
