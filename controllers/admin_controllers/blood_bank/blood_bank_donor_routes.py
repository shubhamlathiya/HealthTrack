from datetime import datetime
import random
import string

from flask import render_template, request, redirect, flash
from werkzeug.security import generate_password_hash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import BLOOD_BANK_DONOR, ADMIN, BLOOD_BANK_ADD_DONOR, BLOOD_BANK_EDIT_DONOR, \
    BLOOD_BANK_DELETE_DONOR, BLOOD_BANK_RESTORE_DONOR
from models.bloodModel import BloodDonor
from models.patientModel import Patient
from models.userModel import User
from utils.config import db
from utils.email_utils import send_email


@admin.route(BLOOD_BANK_DONOR, methods=['GET'], endpoint='blood_bank_donor')
def blood_bank_donor():
    donors = BloodDonor.query.filter_by(is_deleted=False).all()
    deleted_donors = BloodDonor.query.filter_by(is_deleted=True).all()
    return render_template("admin_templates/blood_bank/blood_donor.html",
                           donors=donors,
                           deleted_donors=deleted_donors,
                           datetime=datetime,
                           ADMIN=ADMIN,
                           BLOOD_BANK_ADD_DONOR=BLOOD_BANK_ADD_DONOR,
                           BLOOD_BANK_EDIT_DONOR=BLOOD_BANK_EDIT_DONOR,
                           BLOOD_BANK_DELETE_DONOR=BLOOD_BANK_DELETE_DONOR,
                           BLOOD_BANK_RESTORE_DONOR=BLOOD_BANK_RESTORE_DONOR)


@admin.route(BLOOD_BANK_ADD_DONOR, methods=['POST'], endpoint="add_blood_donor")
def add_blood_donor():
    try:
        # Check if this is an existing patient
        is_existing_patient = request.form.get('is_existing_patient') == 'on'
        patient_id = request.form.get('patient_id') if is_existing_patient else None

        # Validate required fields
        required_fields = ['first_name', 'last_name', 'blood_type', 'gender',
                           'date_of_birth', 'phone', 'email']
        if not all(request.form.get(field) for field in required_fields):
            flash('Please fill in all required fields', 'danger')
            return redirect(request.url)

        # If existing patient, verify patient exists
        if is_existing_patient and patient_id:
            patient = Patient.query.filter_by(patient_id=patient_id, is_deleted=False).first()
            if not patient:
                flash('Patient not found with the provided ID', 'danger')
                return redirect(request.url)

            # Verify patient details match (optional security check)
            if (patient.first_name != request.form['first_name'] or
                    patient.last_name != request.form['last_name']):
                flash('Patient details do not match the provided ID', 'warning')
                return redirect(request.url)

            patient_id = patient.patient_id
        else:
            # Create new user and patient if checkbox is checked
            if request.form.get('create_patient') == 'on':
                # Check if email already exists
                existing_user = User.query.filter_by(email=request.form['email']).first()
                if existing_user:
                    flash('Email already exists in the system', 'danger')
                    return redirect(request.url)

                digits = random.choices(string.digits, k=2)
                specials = random.choices('!@#$%^&*', k=2)
                letters = random.choices(string.ascii_letters, k=4)
                temp_password = ''.join(random.sample(digits + specials + letters, 8))

                # Create new user
                new_user = User(
                    email=request.form['email'],
                    password=generate_password_hash(temp_password),  # Set a default password that should be changed
                    role='patient',
                    status=True,
                    verified=False
                )
                db.session.add(new_user)
                db.session.flush()  # To get the user ID

                # Generate patient ID (you might have your own logic for this)
                last_patient = Patient.query.order_by(Patient.id.desc()).first()
                new_patient_id = last_patient.patient_id + 1 if last_patient else 1000

                # Create new patient
                new_patient = Patient(
                    user_id=new_user.id,
                    patient_id=new_patient_id,
                    first_name=request.form['first_name'],
                    last_name=request.form['last_name'],
                    age=(datetime.now().year - datetime.strptime(request.form['date_of_birth'],
                                                                 '%Y-%m-%d').date().year),
                    address=request.form.get('address'),
                    phone=request.form['phone'],
                    gender=request.form['gender']
                )
                db.session.add(new_patient)
                db.session.flush()

                patient_id = new_patient.patient_id
                body = f"""Welcome to our healthcare Hospital!

                                Your temporary password is: {temp_password}

                                Please change your password after logging in.
                                            """
                send_email("Your New Patient Account", new_user.email, body)

                verification_link = f"http://localhost:5000/auth/verify-email/{new_user.id}"
                send_email('Verify Your Email', new_user.email, verification_link)

        # Create new donor
        new_donor = BloodDonor(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            blood_type=request.form['blood_type'],
            gender=request.form['gender'],
            date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date(),
            phone=request.form['phone'],
            email=request.form['email'],
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            postal_code=request.form.get('postal_code'),
            country=request.form.get('country'),
            status=request.form.get('status', 'Active'),
            last_donation=datetime.strptime(request.form['last_donation'], '%Y-%m-%d').date() if request.form.get(
                'last_donation') else None,
            medical_history=request.form.get('medical_history'),
            emergency_contact_name=request.form.get('emergency_contact_name'),
            emergency_contact_phone=request.form.get('emergency_contact_phone'),
            emergency_contact_relation=request.form.get('emergency_contact_relation'),
            notes=request.form.get('notes'),
            patient_id=patient_id
        )

        # Calculate next eligible date
        if new_donor.last_donation:
            new_donor.calculate_next_eligible()

        db.session.add(new_donor)
        db.session.commit()

        flash(f'Donor {new_donor.first_name} {new_donor.last_name} added successfully!', 'success')

        # If new patient was created, add additional flash message
        if not is_existing_patient and request.form.get('create_patient') == 'on':
            flash(f'Patient account created with ID: {patient_id}. Password reset email sent.', 'info')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding donor: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_DONOR)


@admin.route(BLOOD_BANK_EDIT_DONOR + '/<int:donor_id>', methods=['POST'])
def edit_blood_donor(donor_id):
    donor = BloodDonor.query.get_or_404(donor_id)

    try:
        # Update only the fields that exist in the modal form
        donor.blood_type = request.form['blood_type']
        donor.status = request.form['status']

        # Handle last donation date (optional field)
        last_donation = request.form.get('last_donation')
        donor.last_donation = datetime.strptime(last_donation, '%Y-%m-%d').date() if last_donation else None

        # Handle next eligible date (optional field)
        next_eligible = request.form.get('next_eligible')
        donor.next_eligible = datetime.strptime(next_eligible, '%Y-%m-%d').date() if next_eligible else None

        # Emergency contact info (optional fields)
        donor.emergency_contact_name = request.form.get('emergency_contact_name')
        donor.emergency_contact_phone = request.form.get('emergency_contact_phone')
        donor.emergency_contact_relation = request.form.get('emergency_contact_relation')

        # Notes (optional field)
        donor.notes = request.form.get('notes')

        donor.updated_at = datetime.now()

        # Calculate next eligible date if last donation was updated
        if last_donation:
            donor.calculate_next_eligible()

        db.session.commit()
        flash('Donor information updated successfully!', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating donor: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_DONOR)


@admin.route(BLOOD_BANK_DELETE_DONOR + '/<int:donor_id>', methods=['POST'])
def delete_blood_donor(donor_id):
    donor = BloodDonor.query.get_or_404(donor_id)

    try:
        donor.is_deleted = True
        donor.deleted_at = datetime.now()
        db.session.commit()
        flash('Donor record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting donor: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_DONOR)


@admin.route(BLOOD_BANK_RESTORE_DONOR + '/<int:donor_id>', methods=['POST'])
def restore_blood_donor(donor_id):
    donor = BloodDonor.query.get_or_404(donor_id)

    try:
        donor.is_deleted = False
        donor.deleted_at = None
        db.session.commit()
        flash('Donor record restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring donor: {str(e)}', 'danger')

    return redirect(ADMIN + BLOOD_BANK_DONOR)
