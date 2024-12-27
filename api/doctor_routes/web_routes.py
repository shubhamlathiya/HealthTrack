import datetime

import jwt
from flask import render_template, jsonify, request

from werkzeug.security import check_password_hash

from api.doctor_routes import doctors
from config import mongo


@doctors.route('/login', methods=['GET', 'POST'])
def login_doctors():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        doctors = mongo.db.doctors.find_one({'email': email})
        if not doctors or not check_password_hash(doctors['password'], password):
            return jsonify({'error': 'Invalid email or password'}), 401

        # if not doctors.get('verified'):
        #     return jsonify({'error': 'Email not verified. Redirecting to verification page...'}), 403

        token = jwt.encode({
            'doctors_id': str(doctors['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, 'your_secret_key', algorithm='HS256')

        # print(token)
        return jsonify({'token': token, "doctors": str(doctors['_id'])}), 200

    elif request.method == 'GET':
        return render_template('doctor_templates/doctor_login_templates.html')


@doctors.route('/dashboard')
def doctors_dashboard():  # put application's code here
    return render_template('doctor_templates/doctor_dashboard_templates.html')

@doctors.route('/appointments')
def doctors_appointments():  # put application's code here
    return render_template('doctor_templates/doctor_view_appointments_templates.html')
