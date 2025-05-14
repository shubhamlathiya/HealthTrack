import random
from datetime import datetime

from flask import request, jsonify, render_template
from werkzeug.security import generate_password_hash

from controllers.auth_controllers import auth
from controllers.constant.adminPathConstant import REGISTER
from models.patientModel import Patient
from models.userModel import User, UserRole
from utils.config import db
from utils.email_utils import send_email


# Assuming Patient and User models are already imported from your models
# Also assuming send_email is a utility function to send emails

@auth.route(REGISTER, methods=['GET', 'POST'])
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

            verification_link = f"http://localhost:5000/auth/verify-email/{new_user.id}"
            body_html = render_template("email_templates/templates/verification_mail.html",
                                        verification_link=verification_link,
                                        user_name=new_patient.patient_id)

            send_email('Verify Your Email', new_user.email, body_html)

            return jsonify({'message': 'Patient registered successfully'})

        except Exception as e:
            db.session.rollback()  # Rollback the transaction if there's an error
            return jsonify({'error': str(e)}), 500

    elif request.method == 'GET':
        # If GET request, render registration page
        return render_template('auth_templates/register_templates.html')


@auth.route('/verify-email/<int:patient_id>', methods=['GET'])
def verify_email(patient_id):
    # Retrieve the patient using the patient_id from the database
    patient = User.query.get(patient_id)

    # Check if the patient exists
    if patient:
        # Set the 'verified' field to True
        patient.verified = True

        try:
            # Commit the change to the database
            db.session.commit()
            return render_template('auth_templates/email_verified.html'), 200
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid verification link'}), 400
