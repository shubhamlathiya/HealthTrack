import datetime

from flask import Blueprint, jsonify, request, render_template, session
from werkzeug.security import check_password_hash
import jwt

from controllers.auth_controllers import auth
from utils.config import mongo


@auth.route('/login', methods=['POST'])
def login_patient():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = mongo.db.users.find_one({'email': email})
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid email or password'}), 401

        if not user.get('verified'):
            return jsonify({'message': 'Email not verified. Redirecting to verification page...'}), 403

        if user['status'] == 'true':

            token = jwt.encode({
                'user_id': str(user['_id']),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, 'your_secret_key', algorithm='HS256')

            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            session['role'] = user['role']
            session['name'] = user['name']

            if user['role'] == 'patient':
                redirect_url = '/patient/dashboard'  # Define client dashboard URL
            elif user['role'] == 'admin':
                redirect_url = '/admin/dashboard'
            elif user['role'] == 'doctor':
                redirect_url = '/doctor/dashboard'
            elif user['role'] == 'staff':
                redirect_url = '/staff/dashboard'
            elif user['role'] == 'nurse':
                redirect_url = '/nurse/dashboard'
            elif user['role'] == 'laboratory':
                redirect_url = '/laboratory/dashboard'
            else:
                return jsonify({'message': 'Invalid role. Please contact dashboard.'}), 400

            # print(token)
            return jsonify({'token': token, 'redirect_url': redirect_url}), 200
        else:
            return jsonify({'message': 'Your are DeActive. Please contact Admin'}), 400