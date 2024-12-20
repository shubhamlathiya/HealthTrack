import datetime

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash
import jwt

from api.auth_routes import auth
from config import mongo


@auth.route('/login', methods=['POST'])
def login_patient():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    patient = mongo.db.patients.find_one({'email': email})
    if not patient or not check_password_hash(patient['password'], password):
        return jsonify({'error': 'Invalid email or password'}), 401


    if not patient.get('verified'):
        return jsonify({'error': 'Email not verified. Redirecting to verification page...'}), 403

    token = jwt.encode({
        'patient_id': str(patient['_id']),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, 'your_secret_key', algorithm='HS256')

    return jsonify({'token': token})
