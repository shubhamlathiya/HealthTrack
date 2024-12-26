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


@patients.route('/visits')
def visits():  # put application's code here
    return render_template('patient_templates/visitor_templates.html')

