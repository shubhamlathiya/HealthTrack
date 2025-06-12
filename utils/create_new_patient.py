import random
import string
from datetime import datetime

from flask import render_template
from werkzeug.security import generate_password_hash

from models.doctorModel import Doctor
from models.patientModel import Patient
from models.userModel import User, UserRole
from utils.config import db


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

    # Send welcome and verification emails
    body_html = render_template("email_templates/templates/welcome.html",
                                user_name=f"{new_patient.first_name} {new_patient.last_name}",
                                new_user=new_user,
                                temp_password=temp_password,
                                login_url="http://localhost:5000/")

    # send_email('Welcome to Our Hospital', new_user.email, body_html)

    verification_token = new_user.generate_verification_token()
    verification_link = f"http://localhost:5000/auth/verify-email/{verification_token}"
    body_html = render_template("email_templates/templates/verification_mail.html",
                                verification_link=verification_link,
                                user_name=f"{new_patient.first_name} {new_patient.last_name}")

    # send_email('Verify Your Email', new_user.email, body_html)
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

    # Send welcome and verification emails
    body_html = render_template("email_templates/templates/welcome.html",
                                user_name=f"{new_doctor.first_name} {new_doctor.last_name}",
                                new_user=new_user,
                                temp_password=temp_password,
                                login_url="http://localhost:5000/")

    # send_email('Welcome to Our Hospital', new_user.email, body_html)

    verification_token = new_user.generate_verification_token()
    verification_link = f"http://localhost:5000/auth/verify-email/{verification_token}"
    body_html = render_template("email_templates/templates/verification_mail.html",
                                verification_link=verification_link,
                                user_name=f"{new_doctor.first_name} {new_doctor.last_name}")

    # send_email('Verify Your Email', new_user.email, body_html)

    return new_doctor
