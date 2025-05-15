import random
import string
from datetime import datetime

from flask import render_template
from werkzeug.security import generate_password_hash

from models.patientModel import Patient
from models.userModel import User, UserRole
from utils.config import db
from utils.email_utils import send_email


def create_new_patient(patient_data):
    print(patient_data)
    # Generate temporary password
    digits = random.choices(string.digits, k=2)
    specials = random.choices('!@#$%^&*', k=2)
    letters = random.choices(string.ascii_letters, k=4)
    temp_password = ''.join(random.sample(digits + specials + letters, 8))

    # Create new user
    new_user = User(
        email=patient_data['email'],
        password=generate_password_hash(temp_password),
        role=UserRole.PATIENT,
        status=True,
        verified=False
    )
    db.session.add(new_user)
    db.session.flush()

    current_date = datetime.utcnow()
    year = current_date.year
    month = f"{current_date.month:02d}"
    day = f"{current_date.day:02d}"

    # Generate random 2-digit number for uniqueness
    random_digits = random.randint(10, 99)

    # Create a unique user ID in the format of YYYYMMDDXX
    new_patient_id = f"{year}{month}{day}{random_digits}"

    new_patient = Patient(
        user_id=new_user.id,
        patient_id=new_patient_id,
        first_name=patient_data['first_name'],
        last_name=patient_data['last_name'],
        phone=patient_data['phone'],
        age=patient_data['age'],
        gender = patient_data['gender']
    )
    db.session.add(new_patient)
    db.session.flush()

    # Send welcome and verification emails
    body_html = render_template("email_templates/templates/welcome.html",
                                user_name=f"{new_patient.first_name} {new_patient.last_name}",
                                new_user=new_user,
                                temp_password=temp_password,
                                login_url="http://localhost:5000/")

    send_email('Welcome to Our Hospital', new_user.email, body_html)

    verification_token = new_user.generate_verification_token()
    verification_link = f"http://localhost:5000/auth/verify-email/{verification_token}"
    body_html = render_template("email_templates/templates/verification_mail.html",
                                verification_link=verification_link,
                                user_name=f"{new_patient.first_name} {new_patient.last_name}")

    send_email('Verify Your Email', new_user.email, body_html)
    return new_patient
