from flask import render_template

from api.patients import patients


@patients.route('/')
def hello_world():  # put application's code here
    return render_template('auth_templates/login_templates.html')


@patients.route('/dashboard')
def dashboard():  # put application's code here
    return render_template('patient_templates/patient_dashboard_templates.html')


@patients.route('/appointments')
def appointments():  # put application's code here
    return render_template('patient_templates/patient_view_appointment_templates.html')


@patients.route('/add_appointments')
def add_appointments():  # put application's code here
    return render_template('patient_templates/patient_book_appointment_templates.html')

@patients.route('/visits')
def visits():  # put application's code here
    return render_template('patient_templates/visitor_templates.html')


@patients.route('/prescriptions')
def prescriptions():  # put application's code here
    return render_template('patient_templates/prescription_templates.html')

@patients.route('/upload-patient-reports')
def upload_patient_reports():  # put application's code here
    return render_template('patient_templates/upload_view_patient_reports_templates.html')

@patients.route('/profile')
def profile():  # put application's code here
    return render_template('patient_templates/patient_profile_templates.html')
