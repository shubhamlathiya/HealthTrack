import random
from datetime import datetime, timedelta

from flask import request, jsonify, render_template, flash
from werkzeug.security import generate_password_hash

from controllers.auth_controllers import auth
from controllers.constant.authPathConstant import REGISTER, AUTH, VERIFY_EMAIL_RESEND, VERIFY_EMAIL
from models.doctorModel import Doctor
from models.patientModel import Patient
from models.userModel import User, UserRole
from utils.config import db
from utils.email_utils import send_email
from utils.tokens import verify_token


@auth.route(REGISTER, methods=['GET', 'POST'], endpoint="register_patient")
def register_patient():
    if request.method == 'POST':
        data = request.get_json()  # Get JSON data from request body
        print(data)

        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400

        # Hash the password before storing it
        hashed_password = generate_password_hash(data['password'])

        # Get the current date and generate a unique user ID
        current_date = datetime.utcnow()
        year = current_date.year
        month = f"{current_date.month:02d}"
        day = f"{current_date.day:02d}"

        # Generate random 2-digit number for uniqueness
        random_digits = random.randint(10, 99)

        # Create a unique user ID in the format of YYYYMMDDXX
        unique_user_id = f"{year}{month}{day}{random_digits}"

        # Create the User object to insert into the database
        new_user = User(
            email=data['email'],
            password=hashed_password,
            status=True,  # Assuming 'true' means active
            role=UserRole.PATIENT,  # Assuming it's a patient being registered
            verified=False,  # Set to False until verified
        )

        try:
            # Add the new user to the session and commit it to the database
            db.session.add(new_user)
            db.session.commit()

            # Now that the user is created, create the corresponding Patient record
            new_patient = Patient(
                user_id=new_user.id,  # Foreign Key to User model
                patient_id=unique_user_id,  # Patient ID can be the same as unique_user_id
                first_name=data['first_name'],
                last_name=data['last_name'],
                age=data.get('age', None),
                address=data.get('address', ''),
                phone=data.get('phone', '')
            )

            # Add the new patient to the session and commit it to the database
            db.session.add(new_patient)
            db.session.commit()

            body_html = render_template("email_templates/templates/welcome.html",
                                        user_name=new_patient.patient_id,
                                        new_user=new_user,
                                        temp_password=data['password'],
                                        login_url="http://localhost:5000/")

            send_email('Welcome to HealthTrack Hospital', new_user.email, body_html)

            verification_token = new_user.generate_verification_token()
            verification_link = f"http://localhost:5000/auth/verify-email/{verification_token}"
            body_html = render_template("email_templates/templates/verification_mail.html",
                                        verification_link=verification_link,
                                        user_name=new_patient.patient_id)

            send_email('Verify Your Email', new_user.email, body_html)

            new_user.verification_sent_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Patient registered successfully'})

        except Exception as e:
            db.session.rollback()  # Rollback the transaction if there's an error
            return jsonify({'error': str(e)}), 500

    elif request.method == 'GET':
        # If GET request, render registration page
        return render_template('auth_templates/register_templates.html',
                               AUTH=AUTH,
                               REGISTER=REGISTER)


@auth.route(VERIFY_EMAIL_RESEND, methods=['GET', 'POST'], endpoint="resend_verification")
def resend_verification():
    if request.method == 'POST':
        global data
        email = request.json.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({'error': 'No account found with this email'}), 404

        if user.verified:
            return jsonify({'message': 'Email is already verified'}), 200

        # Prevent spamming - limit to 1 resend every 5 minutes
        last_sent = getattr(user, 'verification_sent_at', None)
        if last_sent and datetime.utcnow() < last_sent + timedelta(minutes=3):
            return jsonify({
                'error': 'Verification email already sent recently. Please check your inbox or wait 3 minutes.'
            }), 429

        if user.role == UserRole.PATIENT:
            patients = Patient.query.filter_by(user_id=user.id).first()
            data = patients.patient_id
            if not data:
                return jsonify({'error': "Patients Not Found"}), 404
        elif user.role == UserRole.DOCTOR:
            doctors = Doctor.query.filter_by(user_id=user.id).first()
            data = doctors.doctor_id
            if not data:
                return jsonify({'error': "Patients Not Found"}), 404
        elif user.role == UserRole.DEPARTMENT_HEAD:
            data = "Department Head"

        # Generate new token and send email
        verification_token = user.generate_verification_token()
        verification_link = f"http://localhost:5000/auth/verify-email/{verification_token}"
        body_html = render_template("email_templates/templates/verification_mail.html",
                                    verification_link=verification_link,
                                    user_name=data)

        send_email('Verify Your Email', user.email, body_html)

        # Update last sent timestamp
        user.verification_sent_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Verification email resent successfully',
            'email': user.email  # Return masked email for display
        }), 200

    return render_template('auth_templates/resend_email_verification_link.html',
                           AUTH=AUTH,
                           VERIFY_EMAIL_RESEND=VERIFY_EMAIL_RESEND)


@auth.route(VERIFY_EMAIL + '/<token>', methods=['GET'], endpoint='verify_email')
def verify_email(token):
    user_id = verify_token(token)
    if not user_id:
        flash('Invalid or expired verification link', 'error')
        return render_template('auth_templates/email_verified.html')

    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return render_template('auth_templates/email_verified.html')

    if user.verified:
        flash('Email already verified', 'info')
        return render_template('auth_templates/email_verified.html')

    user.verified = True
    db.session.commit()
    flash('Email Verified Successfully!', 'success')
    return render_template('auth_templates/email_verified.html')
