from datetime import datetime

from flask import jsonify, render_template, redirect, flash

from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models import Prescription, Appointment
from models.doctorModel import Doctor
from models.patientModel import Patient
from models.userModel import User
from utils.email_utils import send_email


@patients.route('/prescriptions', methods=['GET'])
@token_required
def get_patient_prescriptions(current_user):
    try:
        # Get patient record
        patient = Patient.query.filter_by(user_id=current_user).first()
        if not patient:
            return redirect("/patient/prescriptions")

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
                    'dosage': med.dosage,
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
        return jsonify({'error': str(e)}), 500


@patients.route('/send-prescription-email/<int:prescription_id>', methods=['GET'])
@token_required
def send_prescription_email(current_user, prescription_id):
    # try:
    users = User.query.filter_by(id=current_user).first()
    if not users:
        flash('Users not found', 'danger')
        return redirect("/patient/prescriptions")

    # Verify the prescription belongs to the current user
    patient = Patient.query.filter_by(user_id=current_user).first()
    if not patient:
        flash('Patient not found', 'danger')
        return redirect("/patient/prescriptions")

    prescription = Prescription.query.get(prescription_id)
    if not prescription or prescription.is_deleted:
        flash('Prescription not found', 'danger')
        return redirect("/patient/prescriptions")

    # Check if this prescription belongs to the patient
    appointment = Appointment.query.get(prescription.appointment_id)
    if not appointment or appointment.patient_id != patient.id:
        flash('Unauthorized access', 'danger')
        return redirect("/patient/prescriptions")

    # Get doctor details
    doctor = Doctor.query.filter_by(id=appointment.doctor_id).first()
    if not doctor:
        flash('Doctor not found', 'danger')
        return redirect("/patient/prescriptions")

    # Get clinic information (you might want to store this in a config or database)
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

    send_email(subject, users.email, html_content)

    flash('Prescription email sent successfully', 'success')
    return redirect("/patient/prescriptions")
