import random
import string
from datetime import datetime

from flask import render_template
from werkzeug.security import generate_password_hash

from models.doctorModel import Doctor
from models.patientModel import Patient
from models.userModel import User, UserRole
from utils.config import db
from utils.email_utils import send_email


def generate_id():
    current_date = datetime.utcnow()
    year = current_date.year
    month = f"{current_date.month:02d}"
    day = f"{current_date.day:02d}"
    random_digits = random.randint(10, 99)
    return int(f"{year}{month}{day}{random_digits}")

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

    new_patient = Patient(
        user_id=new_user.id,
        patient_id=generate_id(),
        first_name=patient_data['first_name'],
        last_name=patient_data['last_name'],
        phone=patient_data['phone'],
        age=patient_data['age'],
        gender = patient_data['gender']
    )
    db.session.add(new_patient)
    db.session.flush()

    # Prepare full name for emails
    person_full_name = f"{new_patient.first_name} {new_patient.last_name}".strip()

    # 3. Send Emails
    _send_welcome_and_verification_emails(new_user, person_full_name, temp_password)

    return new_patient


def create_new_doctor(doctor_data):
    """
    Args:
        doctor_data (dict): A dictionary containing doctor's details.
                            Expected keys: 'email', 'first_name', 'last_name', 'age',
                            'gender', 'phone', 'qualification', 'designation',
                            'blood_group', 'address', 'bio'.
    Returns:
        tuple: A tuple containing (new_doctor_object, new_user_object, temporary_password_string).
    """
    # Generate temporary password
    digits = random.choices(string.digits, k=2)
    specials = random.choices('!@#$%^&*', k=2)
    letters = random.choices(string.ascii_letters, k=4)
    temp_password = ''.join(random.sample(digits + specials + letters, 8))

    # 1. Create User
    new_user = User(
        email=doctor_data['email'],
        password=generate_password_hash(temp_password),
        role=UserRole.DOCTOR,
        status=True,  # Assuming newly registered doctors are active
        verified=False
    )
    db.session.add(new_user)
    db.session.flush()  # Flush to get new_user.id before creating Doctor

    # 2. Create Doctor
    new_doctor = Doctor(
        user_id=new_user.id,
        doctor_id=generate_id(),  # Generate unique doctor ID
        first_name=doctor_data['first_name'],
        last_name=doctor_data['last_name'],
        age=doctor_data['age'],
        gender=doctor_data['gender'],
        phone=doctor_data['phone'],
        qualification=doctor_data['qualification'],
        designation=doctor_data['designation'],
        blood_group=doctor_data['blood_group'],
        address=doctor_data['address'],
        bio=doctor_data.get('bio', ''),  # Bio is optional
        profile_picture=None  # Profile picture will be handled by the caller
    )
    db.session.add(new_doctor)
    db.session.flush()  # Flush to get new_doctor.id if needed by caller (e.g., for availability)

    # Prepare full name for emails
    person_full_name = f"{new_doctor.first_name} {new_doctor.last_name}".strip()

    # 3. Send Emails
    _send_welcome_and_verification_emails(new_user, person_full_name, temp_password)

    return new_doctor


def _send_welcome_and_verification_emails(user: User, person_name: str, temp_password: str):
    """
    Helper to send both welcome and email verification emails.
    Requires an active Flask application context for current_app.
    """
    # Get base URL from current_app config or default (crucial for deployment)
    base_url = 'http://localhost:5000'

    # --- Send Welcome Email ---
    welcome_body_html = render_template("email_templates/templates/welcome.html",
                                        user_name=person_name,
                                        new_user=user,
                                        temp_password=temp_password,
                                        login_url=f"{base_url}/auth/login")  # Use actual login route

    send_email('Welcome to Our Hospital', user.email, welcome_body_html)

    # --- Send Verification Email ---
    verification_token = user.generate_verification_token()  # Assuming User model has this method
    verification_link = f"{base_url}/auth/verify-email/{verification_token}"
    verification_body_html = render_template("email_templates/templates/verification_mail.html",
                                             verification_link=verification_link,
                                             user_name=person_name)

    send_email('Verify Your Email', user.email, verification_body_html)
