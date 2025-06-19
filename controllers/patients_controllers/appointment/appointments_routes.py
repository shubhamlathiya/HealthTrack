from datetime import datetime, timedelta, date

from flask import render_template, request, jsonify, flash, redirect
from sqlalchemy import and_, or_, not_

from controllers.constant.patientPathConstant import VIEW_APPOINTMENT, PATIENT, BOOK_APPOINTMENT, \
    RESCHEDULE_APPOINTMENT, CANCEL_APPOINTMENT
from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models.appointmentModel import Appointment, AppointmentTreatment, Survey
from models.departmentModel import Department
from models.doctorModel import Doctor
from models.patientModel import Patient
from models.treatmentModel import Treatment
from models.userModel import User, UserRole
from utils.config import db
from utils.email_utils import send_email


@patients.route(VIEW_APPOINTMENT, methods=['GET'], endpoint="view_appointment")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def view_appointment(current_user):
    patients = Patient.query.filter_by(user_id=current_user).first()

    appointments = Appointment.query.filter_by(
        patient_id=patients.id
    ).order_by(
        Appointment.date.desc()
    ).all()

    return render_template("patient_templates/appointment/list_appointments.html",
                           appointments=appointments,
                           patient=patients,
                           date=date,
                           PATIENT=PATIENT,
                           BOOK_APPOINTMENT=BOOK_APPOINTMENT
                           )


@patients.route(BOOK_APPOINTMENT, methods=['GET'], endpoint="book_appointment")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def book_appointment(current_user):
    # Get all active departments
    departments = Department.query.filter_by(is_deleted=False, status=True).all()


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


@patients.route(BOOK_APPOINTMENT, methods=['POST'], endpoint="create_appointment")
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


@patients.route(RESCHEDULE_APPOINTMENT + '/<int:appointment_id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def reschedule_appointment(current_user, appointment_id):
    try:
        # Get the original appointment
        original_appointment = Appointment.query.get_or_404(appointment_id)
        patient = Patient.query.filter_by(user_id=current_user.id).first()

        # Verify ownership
        if not patient or original_appointment.patient_id != patient.id:
            flash('Unauthorized access to appointment', 'error')
            return redirect(PATIENT + VIEW_APPOINTMENT)

        # Only allow rescheduling of scheduled appointments
        if original_appointment.status != 'scheduled':
            flash('Only scheduled appointments can be rescheduled', 'error')
            return redirect(PATIENT + VIEW_APPOINTMENT)

        # Get form data
        new_date_str = request.form.get('date')
        time_slot_str = request.form.get('time_slot')
        reason = request.form.get('reason', original_appointment.reason)

        # Validate inputs
        if not new_date_str or not time_slot_str:
            flash('Please select both date and time slot', 'error')
            return redirect(PATIENT + VIEW_APPOINTMENT)

        try:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(time_slot_str, '%H:%M:%S').time()
        except ValueError:
            flash('Invalid date or time format', 'error')
            return redirect(PATIENT + VIEW_APPOINTMENT)

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
            return redirect(PATIENT + VIEW_APPOINTMENT)

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
        return redirect(PATIENT + VIEW_APPOINTMENT)

    except Exception as e:
        db.session.rollback()
        flash('An error occurred while rescheduling your appointment', 'error')
        return redirect(PATIENT + VIEW_APPOINTMENT)


@patients.route(CANCEL_APPOINTMENT + '/<int:appointment_id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def cancel_appointment(current_user, appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    user = User.query.filter_by(id=current_user).first()
    patient = Patient.query.filter_by(user_id=current_user).first()

    if appointment.patient_id != patient.id:
        flash('Unauthorized to cancel this appointment.', 'danger')
        return redirect(PATIENT + VIEW_APPOINTMENT)

    if appointment.status != 'scheduled':
        flash('Only scheduled appointments can be canceled.', 'warning')
        return redirect(PATIENT + VIEW_APPOINTMENT)

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
    return redirect(PATIENT + VIEW_APPOINTMENT)


# --- New Survey Routes ---

# Route to display the survey form
@patients.route('/survey/<int:appointment_id>', methods=['GET'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def take_survey(current_user, appointment_id):
    # 1. Fetch the Appointment first to ensure it exists and belongs to the patient
    appointment = Appointment.query.get(appointment_id)
    patient = Patient.query.filter_by(user_id=current_user).first()
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(PATIENT + VIEW_APPOINTMENT)

    # 2. Ensure the appointment belongs to the current logged-in patient
    # current_user from token_required should be the patient object or their ID
    if int(appointment.patient_id) != int(patient.id):  # Assuming current_user has an 'id' attribute
        flash('You are not authorized to access this survey for this appointment.', 'danger')
        return redirect(PATIENT + VIEW_APPOINTMENT)

    # 3. Check if the appointment status is 'completed'
    if appointment.status != 'Completed':
        flash('Feedback can only be provided for completed appointments.', 'info')
        return redirect(PATIENT + VIEW_APPOINTMENT)

    # 4. Check if a survey already exists and has been taken for this specific appointment
    # We should query for a survey linked to THIS appointment ID
    survey = Survey.query.filter_by(appointment_id=appointment_id).first()

    if survey and survey.is_taken:
        flash('You have already submitted feedback for this appointment. Thank you!', 'info')
        # You might want to pass the survey object to the template if you want to show past answers
        return render_template(
            'patient_templates/appointment/survey.html',
            survey_taken=True,
            survey_data=survey,  # Pass the existing survey data
            appointment=appointment,
            PATIENT=PATIENT,
            VIEW_APPOINTMENT=VIEW_APPOINTMENT            # Pass appointment details if needed
        )

    # 5. If no survey exists or it's not taken, create a new one (if not already existing and not taken)
    # This ensures a survey record is created when the patient first attempts to give feedback
    # It also handles cases where a survey wasn't automatically created upon completion.
    if not survey:
        try:
            survey = Survey(
                appointment_id=appointment.id,
                patient_id=patient.id,
                # survey_token will be auto-generated by the model default
            )
            db.session.add(survey)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error initiating survey: {e}', 'danger')
            return redirect(PATIENT + VIEW_APPOINTMENT)

    # If we reach here, it means we have an untaken survey (either existing or newly created)
    # Pass the survey's unique token to the template for form submission
    # The template relies on 'survey_token' for the form action, so we must provide it.
    return render_template(
        'patient_templates/appointment/survey.html',
        survey_taken=False,
        survey_token=survey.survey_token,  # This is crucial for the POST route
        appointment=appointment,
        PATIENT=PATIENT,
        VIEW_APPOINTMENT=VIEW_APPOINTMENT
        # Pass appointment details if needed
    )


# Route to handle survey submission
@patients.route('/survey/<string:survey_token>/submit', methods=['POST'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def submit_survey(current_user, survey_token):
    survey = Survey.query.filter_by(survey_token=survey_token).first()

    if not survey:
        flash('Invalid survey link.', 'danger')
        return redirect(PATIENT + VIEW_APPOINTMENT)

    patient = Patient.query.filter_by(user_id=current_user).first()
    if survey.patient_id != patient.id:
        flash('You are not authorized to submit this survey.', 'danger')
        return redirect(PATIENT + VIEW_APPOINTMENT)

    if survey.is_taken:
        flash('You have already submitted feedback for this appointment. Thank you!', 'info')
        return redirect(PATIENT + VIEW_APPOINTMENT)

    try:
        # Get data from the form
        overall_experience = request.form.get('overall_experience', type=int)
        doctor_communication = request.form.get('doctor_communication', type=int)
        comments = request.form.get('comments')

        # Basic validation (add more robust validation as needed)
        if overall_experience is None or not (1 <= overall_experience <= 5):
            flash('Please select an overall experience rating.', 'warning')
            return redirect(PATIENT + VIEW_APPOINTMENT)
        if doctor_communication is None or not (1 <= doctor_communication <= 5):
            flash('Please select a doctor communication rating.', 'warning')
            return redirect(PATIENT + VIEW_APPOINTMENT)

        # Update the survey record
        survey.overall_experience = overall_experience
        survey.doctor_communication = doctor_communication
        survey.comments = comments
        survey.is_taken = True
        survey.submitted_at = datetime.now()

        db.session.commit()
        flash('Thank you for your valuable feedback!', 'success')
        return redirect(PATIENT + VIEW_APPOINTMENT)

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while submitting your feedback: {e}', 'danger')
        return redirect(PATIENT + VIEW_APPOINTMENT)
