from datetime import datetime
import random

from bson import ObjectId
from flask import jsonify, request, render_template
from werkzeug.security import generate_password_hash

from controllers.auth_controllers import auth
from controllers.constant.adminPathConstant import REGISTER
from utils.config import mongo
from utils.email_utils import send_email


@auth.route(REGISTER, methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        existing_patient = mongo.db.users.find_one({'email': data['email']})
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
            'user_id': unique_patient_id,
            'name': data['name'],
            'email': data['email'],
            'password': hashed_password,
            'created_at': current_date,
            'status': 'true',
            'role' : "patient"
        }
        patient_id = mongo.db.users.insert_one(patient).inserted_id

        verification_link = f"http://localhost:5000/auth/verify-email/{str(patient_id)}"
        send_email('Verify Your Email', data['email'], verification_link)

        return jsonify({'message': 'Patient registered successfully'})
    elif request.method == 'GET':
        return render_template('auth_templates/register_templates.html')


@auth.route('/verify-email/<patient_id>', methods=['GET'], endpoint='verify_email')
def verify_email(patient_id):
    patient = mongo.db.users.find_one({'_id': ObjectId(patient_id)})
    if patient:
        mongo.db.users.update_one({'_id': ObjectId(patient_id)}, {'$set': {'verified': True}})
        return jsonify({'message': 'Email verified successfully'})
    return jsonify({'error': 'Invalid verification link'}), 400
