from datetime import datetime
import random

from bson import ObjectId
from flask import jsonify, request
from werkzeug.security import generate_password_hash

from api.auth_routes import auth
from config import mongo
from email_utils import send_email


@auth.route('/register', methods=['POST'])
def register_patient():
    data = request.get_json()
    existing_patient = mongo.db.patients.find_one({'email': data['email']})
    if existing_patient:
        return jsonify({'error': 'Email already registered'}), 400

    hashed_password = generate_password_hash(data['password'])

    current_date = datetime.utcnow()
    year = current_date.year
    month = f"{current_date.month:02d}"
    day = f"{current_date.day:02d}"

    # Generate random 2-digit number
    random_digits = random.randint(10, 99)

    unique_patient_id = f"{year}{month}{day}{random_digits}"
    patient = {
        'patient_id': unique_patient_id,
        'name': data['name'],
        'email': data['email'],
        'password': hashed_password,
        'created_at': current_date
    }
    patient_id = mongo.db.patients.insert_one(patient).inserted_id

    verification_link = f"http://localhost:5000/auth/verify-email/{str(patient_id)}"
    send_email('Verify Your Email', data['email'], verification_link)

    return jsonify({'message': 'Patient registered successfully'})


@auth.route('/verify-email/<patient_id>', methods=['GET'])
def verify_email(patient_id):
    patient = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
    if patient:
        mongo.db.patients.update_one({'_id': ObjectId(patient_id)}, {'$set': {'verified': True}})
        return jsonify({'message': 'Email verified successfully'})
    return jsonify({'error': 'Invalid verification link'}), 400
