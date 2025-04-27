import datetime

import jwt
from flask import jsonify, request, session
from werkzeug.security import check_password_hash

from controllers.auth_controllers import auth
from controllers.constant.adminPathConstant import LOGIN
from models.userModel import User


@auth.route(LOGIN, methods=['POST'] , endpoint='login')
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Query the database using SQLAlchemy to find the user by email
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            return jsonify({'error': 'Invalid email or password'}), 401

        if not user.verified:
            return jsonify({'message': 'Email not verified. Redirecting to verification page...'}), 403

        if user.status:  # Assuming 'status' is a boolean or a 1/0 value (active/inactive)
            # Generate a JWT token that expires in 1 hour
            token = jwt.encode({
                'user_id': str(user.id),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=10)
            }, 'your_secret_key', algorithm='HS256')

            # Store user data in session
            session['user_id'] = str(user.id)
            session['email'] = user.email
            session['role'] = user.role

            # Redirect based on user role
            if user.role == 'patient':
                redirect_url = '/patients/dashboard'
            elif user.role == 'admin':
                redirect_url = '/admin/dashboard'
            elif user.role == 'doctor':
                redirect_url = '/doctor/dashboard'
            elif user.role == 'staff':
                redirect_url = '/staff/dashboard'
            elif user.role == 'nurse':
                redirect_url = '/nurse/dashboard'
            elif user.role == 'laboratory':
                redirect_url = '/laboratory/dashboard'
            else:
                return jsonify({'message': 'Invalid role. Please contact dashboard.'}), 400

            return jsonify({'token': token, 'redirect_url': redirect_url}), 200
        else:
            return jsonify({'message': 'Your account is inactive. Please contact Admin'}), 400
