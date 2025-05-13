from flask import render_template, request, flash, redirect
from datetime import datetime

from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models.bloodModel import BloodDonor
from models.appointmentModel import Appointment
from models.patientModel import Patient
from utils.config import db


@patients.route('/blood-donors', methods=['GET'], endpoint='view_blood_donors')
@token_required
def view_blood_donors(current_user):
    # Get all active blood donors
    donors = BloodDonor.query.filter_by(is_deleted=False, status='Active').all()
    return render_template("patient_templates/blood_donor/blood_donors.html",
                           donors=donors,
                           datetime=datetime)


@patients.route('/request-donor/<int:donor_id>', methods=['GET', 'POST'], endpoint='request_blood_donor')
@token_required
def request_blood_donor(current_user, donor_id):
    donor = BloodDonor.query.get_or_404(donor_id)

    if request.method == 'POST':
        try:
            # Get current patient (assuming you have patient authentication)
            patient_id = request.form.get('patient_id')
            patient = Patient.query.get(patient_id)

            if not patient:
                flash('Patient not found', 'danger')
                return redirect(url_for('patient.view_blood_donors'))

            # Validate form data
            required_fields = ['appointment_date', 'appointment_time', 'reason']
            if not all(request.form.get(field) for field in required_fields):
                flash('Please fill in all required fields', 'danger')
                return redirect(url_for('patient.request_blood_donor', donor_id=donor_id))

            # Create appointment
            appointment_datetime = datetime.strptime(
                f"{request.form['appointment_date']} {request.form['appointment_time']}",
                '%Y-%m-%d %H:%M'
            )

            new_appointment = Appointment(
                patient_id=patient.patient_id,
                donor_id=donor.donor_id,
                appointment_datetime=appointment_datetime,
                reason=request.form['reason'],
                status='Pending',
                created_at=datetime.now()
            )

            db.session.add(new_appointment)
            db.session.commit()

            # Here you would typically send a notification to the donor
            # For example: send_donor_request_email(donor, patient, new_appointment)

            flash('Appointment request sent successfully! The donor will respond soon.', 'success')
            return redirect(url_for('patient.view_appointments'))

        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid date/time format: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating appointment: {str(e)}', 'danger')

    return render_template("patient_templates/request_donor.html",
                           donor=donor,
                           datetime=datetime)


@patients.route('/appointments', methods=['GET'], endpoint='view_appointments')
@token_required
def view_appointments(current_user):
    # Get current patient's appointments
    patient_id = request.args.get('patient_id')  # In real app, get from session
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
        Appointment.appointment_datetime.desc()).all()

    return render_template("patient_templates/appointments.html",
                           appointments=appointments,
                           datetime=datetime)