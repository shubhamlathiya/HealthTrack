from datetime import datetime

from flask import jsonify, render_template, redirect, flash

from controllers.constant.patientPathConstant import VIEW_PRESCRIPTIONS, SEND_PRESCRIPTION_EMAIL
from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models import Prescription, Appointment
from models.doctorModel import Doctor
from models.patientModel import Patient
from models.userModel import User, UserRole
from utils.email_utils import send_email


@patients.route(VIEW_PRESCRIPTIONS, methods=['GET'], endpoint="view_patient_prescriptions")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def view_patient_prescriptions(current_user):
    """
    Renders the view for a patient's prescriptions, fetching all
    prescriptions associated with their appointments.
    """
    try:
        # Get patient record
        # Assuming current_user is the User object, not just the ID.
        # If current_user is just the ID, it should be current_user_id
        patient = Patient.query.filter_by(user_id=current_user).first()
        if not patient:
            flash('Patient record not found.', 'danger')
            return redirect("/") # Redirect to a relevant dashboard or error page

        # Get all appointments for the patient
        appointments = Appointment.query.filter_by(patient_id=patient.id).all()
        appointment_ids = [appointment.id for appointment in appointments]

        # Get all prescriptions for these appointments
        prescriptions = Prescription.query.filter(
            Prescription.appointment_id.in_(appointment_ids),
            Prescription.is_deleted == False
        ).all()

        # Prepare the response data
        prescriptions_data = []
        for prescription in prescriptions:
            prescription_data = {
                'id': prescription.id,
                'appointment_id': prescription.appointment_id,
                'appointment_date': prescription.appointment.date.isoformat() if prescription.appointment else '',
                'doctor_name': f"{prescription.appointment.doctor.first_name} {prescription.appointment.doctor.last_name}" if prescription.appointment and prescription.appointment.doctor else '',
                'notes': prescription.notes,
                'status': prescription.status,
                'created_at': prescription.created_at.isoformat(),
                'medications': [],
                'test_reports': []
            }

            # Add medications
            for med in prescription.medications:
                medication = {
                    'name': med.name,
                    'days': med.days, # Changed from med.dosage to med.days
                    'meal_instructions': med.meal_instructions,
                    'timing': [t.timing for t in med.timings]
                }
                prescription_data['medications'].append(medication)

            # Add test reports
            for report in prescription.test_reports:
                test_report = {
                    'report_name': report.report_name,
                    'report_notes': report.report_notes,
                    'price': report.price,
                    'status': report.status,
                    'file_path': report.file_path
                }
                prescription_data['test_reports'].append(test_report)

            prescriptions_data.append(prescription_data)

        # Render HTML template with the prescriptions data
        return render_template('patient_templates/appointment/patient_prescriptions.html',
                               prescriptions=prescriptions_data,
                               patient_name=f"{patient.first_name} {patient.last_name}")

    except Exception as e:
        # Log the exception for debugging purposes
        print(f"Error viewing patient prescriptions: {e}")
        flash('An error occurred while fetching prescriptions. Please try again later.', 'danger')
        return redirect("/patient/dashboard") # Redirect to a safe page on error


@patients.route(SEND_PRESCRIPTION_EMAIL + '/<int:prescription_id>', methods=['GET'], endpoint="send_prescription_email")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def send_prescription_email(current_user, prescription_id):
    """
    Sends a prescription as an email to the current patient.
    """
    try:
        # Assuming current_user is the User object, not just the ID.
        users_user_obj = User.query.filter_by(id=current_user).first()
        if not users_user_obj:
            flash('User account not found.', 'danger')
            return redirect("/patient/prescriptions")

        # Verify the prescription belongs to the current user
        patient = Patient.query.filter_by(user_id=current_user).first()
        if not patient:
            flash('Patient record not found.', 'danger')
            return redirect("/patient/prescriptions")

        prescription = Prescription.query.get(prescription_id)
        if not prescription or prescription.is_deleted:
            flash('Prescription not found or is deleted.', 'danger')
            return redirect("/patient/prescriptions")

        # Check if this prescription belongs to the patient
        appointment = Appointment.query.get(prescription.appointment_id)
        if not appointment or appointment.patient_id != patient.id:
            flash('Unauthorized access to prescription.', 'danger')
            return redirect("/patient/prescriptions")

        # Get doctor details
        doctor = Doctor.query.filter_by(id=appointment.doctor_id).first()
        if not doctor:
            flash('Associated doctor not found.', 'danger')
            return redirect("/patient/prescriptions")

        # Get clinic information (consider storing this in a config or database)
        clinic_info = {
            'name': 'HealthTrack',
            'address': '123 Medical Drive, Health City, HC 12345',
            'phone': '(123) 456-7890',
            'email': 'contact@healthtrack.com'
        }

        # Prepare email content
        subject = f"Your Prescription from {clinic_info['name']} - #{prescription.id}"

        # Render the HTML email template
        html_content = render_template(
            'email_templates/templates/prescription_mail.html',
            clinic_name=clinic_info['name'],
            clinic_address=clinic_info['address'],
            clinic_phone=clinic_info['phone'],
            clinic_email=clinic_info['email'],
            patient_name=f"{patient.first_name} {patient.last_name}",
            prescription=prescription,
            doctor_name=f"{doctor.first_name} {doctor.last_name}",
            current_year=datetime.now().year
        )

        send_email(subject, users_user_obj.email, html_content) # Use users_user_obj.email for the recipient

        flash('Prescription email sent successfully.', 'success')
        return redirect(VIEW_PRESCRIPTIONS)

    except Exception as e:
        print(f"Error sending prescription email: {e}")
        flash('An error occurred while sending the prescription email. Please try again later.', 'danger')
        return redirect(VIEW_PRESCRIPTIONS)