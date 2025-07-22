import datetime

import jwt
from flask import jsonify, request, session
from werkzeug.security import check_password_hash

from controllers.auth_controllers import auth
from controllers.constant.adminPathConstant import ADMIN_DASHBOARD
from controllers.constant.authPathConstant import LOGIN
from controllers.constant.departmentPathConstant import DEPARTMENT_DASHBOARD
from controllers.constant.doctorPathConstant import DOCTOR_DASHBOARD
from controllers.constant.laboratoryPathConstant import LABORATORY_DASHBOARD
from controllers.constant.nursePathConstant import NURSE_DASHBOARD
from controllers.constant.patientPathConstant import PATIENT_DASHBOARD
from controllers.constant.staffPathConstant import STAFF_DASHBOARD
from models.userModel import User, UserRole


@auth.route(LOGIN, methods=['POST'] , endpoint='login')
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Query the database using SQLAlchemy to find the user by email
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            return jsonify({'errors': 'Invalid email or password'}), 401

        if not user.verified:
            redirect_url = f"/auth/verify-email/resend?email={email}"
            return jsonify({'redirect_url': redirect_url,
                            'message': 'Email not verified. Redirecting to verification page...'}), 403

        if user.status:  # Assuming 'status' is a boolean or a 1/0 value (active/inactive)
            # Generate a JWT token that expires in 1 hour
            token = jwt.encode({
                'user_id': str(user.id),
                'role': user.role.name,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=10)
            }, 'your_secret_key', algorithm='HS256')

            # Store user data in session
            session['user_id'] = str(user.id)
            session['email'] = user.email
            session["role"] = user.role.name  # or user.role_id
            print(user.role.name)
            # Redirect based on user role
            if user.role == UserRole.PATIENT:
                redirect_url = PATIENT_DASHBOARD
            elif user.role == UserRole.DEPARTMENT_HEAD:
                redirect_url = DEPARTMENT_DASHBOARD
            elif user.role == UserRole.ADMIN:
                redirect_url = ADMIN_DASHBOARD
            elif user.role == UserRole.DOCTOR:
                redirect_url = DOCTOR_DASHBOARD
            elif user.role == UserRole.STAFF:
                redirect_url = STAFF_DASHBOARD
            elif user.role == UserRole.NURSE:
                redirect_url = NURSE_DASHBOARD
            elif user.role == UserRole.LABORATORIST:
                redirect_url = LABORATORY_DASHBOARD
            else:
                return jsonify({'message': 'Invalid role. Please contact dashboard.'}), 400

            return jsonify({'token': token, 'redirect_url': redirect_url}), 200
        else:
            return jsonify({'message': 'Your account is inactive. Please contact Admin'}), 400
