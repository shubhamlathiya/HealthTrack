import random
import string
from datetime import datetime, timedelta
from sqlite3 import IntegrityError

from flask import render_template, flash, redirect, request
from werkzeug.security import generate_password_hash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import (
    BLOOD_BANK_ISSUED, BLOOD_BANK_DELETE_ISSUED,
    BLOOD_BANK_ADD_ISSUED, BLOOD_BANK_RESTORE_ISSUED,
    BLOOD_BANK_EDIT_ISSUED, ADMIN
)
from middleware.auth_middleware import token_required
from models.bloodModel import BloodIssuance, BloodProduct
from models.patientModel import Patient, PatientPayment
from models.userModel import User
from utils.config import db
from utils.email_utils import send_email


def calculate_expiry_date(component_type):
    today = datetime.utcnow().date()
    expiry_days = {
        'Whole Blood': 35,
        'Red Blood Cells': 42,
        'Plasma': 365,
        'Platelets': 5,
        'Cryoprecipitate': 365
    }.get(component_type, 1)
    return today + timedelta(days=expiry_days)


def generate_temp_password():
    digits = random.choices(string.digits, k=2)
    specials = random.choices('!@#$%^&*', k=2)
    letters = random.choices(string.ascii_letters, k=4)
    return ''.join(random.sample(digits + specials + letters, 8))


# Helper Functions
def generate_issue_id():
    """Generate unique issue ID with timestamp and random string"""
    now = datetime.now()
    return f"ISSUE-{now.strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"


def check_patient_exists(patient_id):
    """Check if patient exists in database"""
    return Patient.query.filter_by(id=patient_id, is_deleted=False).first()


def create_payment_record(issuance, form_data):
    """Create payment record for patient"""
    payment = PatientPayment(
        patient_id=issuance.patient_id,
        amount=float(form_data.get('payment_amount', 0)),
        status=form_data.get('payment_status', 'unpaid'),
        payment_date=datetime.strptime(form_data['payment_date'], '%Y-%m-%d').date() if form_data.get(
            'payment_date') else None,
        room_charge_id=form_data.get('room_charge_id'),
        remarks=form_data.get('payment_remarks', 'Blood product issuance')
    )
    db.session.add(payment)
    return payment


# Routes
@admin.route(BLOOD_BANK_ISSUED, methods=['GET'])
def blood_bank_issued():
    issuances = BloodIssuance.query.filter_by(is_deleted=False).order_by(BloodIssuance.issue_date.desc()).all()
    deleted_issuances = BloodIssuance.query.filter_by(is_deleted=True).order_by(BloodIssuance.deleted_at.desc()).all()

    # Update status for any pending issuances with past transfusion dates
    for issuance in issuances:
        if issuance.status == 'Pending' and issuance.transfusion_date and issuance.transfusion_date < datetime.now().date():
            issuance.status = 'Completed'
            db.session.commit()

    return render_template("admin_templates/blood_bank/blood_issued.html",
                           issuances=issuances,
                           deleted_issuances=deleted_issuances,
                           ADMIN=ADMIN,
                           BLOOD_BANK_ADD_ISSUED=BLOOD_BANK_ADD_ISSUED,
                           BLOOD_BANK_EDIT_ISSUED=BLOOD_BANK_EDIT_ISSUED,
                           BLOOD_BANK_DELETE_ISSUED=BLOOD_BANK_DELETE_ISSUED,
                           BLOOD_BANK_RESTORE_ISSUED=BLOOD_BANK_RESTORE_ISSUED)


@admin.route(BLOOD_BANK_ADD_ISSUED, methods=['POST'])
@token_required
def add_blood_issuance(current_user):
    try:
        # Check if this is an existing patient
        is_existing_patient = request.form.get('is_existing_patient') == 'on'
        patient_id = request.form.get('patient_id') if is_existing_patient else None

        # Validate required fields
        required_fields = ['patient_name', 'blood_type', 'component_type', 'quantity', 'issue_date']
        if not all(request.form.get(field) for field in required_fields):
            flash('Please fill in all required fields', 'danger')
            return redirect(request.url)

            # Convert quantity to integer
        try:
            quantity = int(request.form['quantity'])
            if quantity <= 0:
                flash('Quantity must be a positive number', 'danger')
                return redirect(request.url)
        except ValueError:
            flash('Invalid quantity value', 'danger')
            return redirect(request.url)

        # Find available blood product (FIFO - oldest first)
        existing_product = BloodProduct.query.filter(
            BloodProduct.blood_type == request.form['blood_type'],
            BloodProduct.component_type == request.form['component_type'],
            BloodProduct.quantity >= quantity
        ).order_by(BloodProduct.expiry_date.asc()).first()

        if not existing_product:
            # Check if product exists but insufficient quantity
            available_product = BloodProduct.query.filter(
                BloodProduct.blood_type == request.form['blood_type'],
                BloodProduct.component_type == request.form['component_type']
            ).first()

            if available_product:
                flash(f'Not enough inventory. Only {available_product.quantity} units available', 'danger')
            else:
                flash(f"No available {request.form['blood_type']} {request.form['component_type']} found in inventory",
                      'danger')
            return redirect(request.url)
        # Patient verification
        if is_existing_patient and patient_id:
            patient = Patient.query.filter_by(patient_id=patient_id, is_deleted=False).first()
            if not patient:
                flash('Patient not found with the provided ID', 'danger')
                return redirect(request.url)

            if f"{patient.first_name} {patient.last_name}" != request.form['patient_name']:
                flash('Patient name does not match the provided ID', 'warning')
                return redirect(request.url)
        else:
            # Create new patient if requested
            if request.form.get('create_patient') == 'on' and request.form.get('patient_email'):
                if User.query.filter_by(email=request.form['patient_email']).first():
                    flash('Email already exists in the system', 'danger')
                    return redirect(request.url)

                temp_password = generate_temp_password()
                new_user = User(
                    email=request.form['patient_email'],
                    password=generate_password_hash(temp_password),
                    role='patient',
                    status=True,
                    verified=False
                )
                db.session.add(new_user)
                db.session.flush()

                # Generate patient ID
                last_patient = Patient.query.order_by(Patient.patient_id.desc()).first()
                new_patient_id = last_patient.patient_id + 1 if last_patient else 1000

                # Create patient record
                name_parts = request.form['patient_name'].split(maxsplit=1)
                new_patient = Patient(
                    user_id=new_user.id,
                    patient_id=new_patient_id,
                    first_name=name_parts[0],
                    last_name=name_parts[1] if len(name_parts) > 1 else '',
                    age=request.form.get('patient_age'),
                    phone=request.form.get('patient_phone'),
                    gender=request.form.get('patient_gender')
                )
                db.session.add(new_patient)
                db.session.flush()
                patient_id = new_patient.patient_id

                body_html = render_template("email_templates/templates/welcome.html",
                                            user_name=new_patient.patient_id,
                                            new_user=new_user,
                                            temp_password=temp_password,
                                            login_url="http://localhost:5000/")

                send_email('Welcome to HealthTrack Hospital', new_user.email, body_html)

                verification_link = f"http://localhost:5000/auth/verify-email/{new_user.id}"
                body_html = render_template("email_templates/templates/verification_mail.html",
                                            verification_link=verification_link,
                                            user_name=new_patient.patient_id)

                send_email('Verify Your Email', new_user.email, body_html)

                # Reduce blood product quantity
        existing_product.quantity -= quantity
        if existing_product.quantity < 0:
            flash('Inventory inconsistency detected: quantity would go negative.', 'danger')
            db.session.rollback()
            return redirect(request.url)
        # Create issuance record
        new_issuance = BloodIssuance(
            issue_id=generate_issue_id(),
            patient_id=patient_id,
            patient_name=request.form['patient_name'],
            patient_age=int(request.form.get('patient_age', 0)) if request.form.get('patient_age') else None,
            patient_gender=request.form.get('patient_gender'),
            blood_product_id=existing_product.product_code,
            blood_type=request.form['blood_type'],
            component_type=request.form['component_type'],
            quantity=int(request.form['quantity']),
            issue_date=datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date(),
            status=request.form.get('status', 'Pending'),
            transfusion_date=datetime.strptime(request.form['transfusion_date'], '%Y-%m-%d').date() if request.form.get(
                'transfusion_date') else None,
            issue_reason=request.form.get('issue_reason'),
            remarks=request.form.get('remarks'),
            issued_by=current_user,
            blood_product=existing_product
        )
        db.session.add(new_issuance)

        # Create payment if applicable
        if patient_id and request.form.get('payment_amount'):
            new_patient = Patient.query.filter_by(patient_id=patient_id, is_deleted=False).first()
            payment = PatientPayment(
                patient_id=new_patient.id,
                amount=float(request.form['payment_amount']),
                status=request.form.get('payment_status', 'unpaid'),
                payment_date=datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date() if request.form.get(
                    'payment_date') else None,
                remarks=request.form.get('payment_remarks', 'Blood product issuance')
            )
            db.session.add(payment)
            db.session.flush()
            new_issuance.payment_id = payment.id

        db.session.commit()

        flash_messages = [
            f'Blood issued successfully!',
            f'Product ID: {existing_product.product_code}',
            f'Batch Number: {existing_product.batch_number}',
            f'Remaining Quantity: {existing_product.quantity}'
        ]

        if not is_existing_patient and request.form.get('create_patient') == 'on':
            flash_messages.append(f'Patient account created with ID: {patient_id}')

        for msg in flash_messages:
            flash(msg, 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except IntegrityError as e:
        db.session.rollback()
        flash(f'Database error: Please check all fields and try again', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding issuance record: {str(e)}', 'danger')

    return redirect(ADMIN + BLOOD_BANK_ISSUED)


@admin.route(BLOOD_BANK_EDIT_ISSUED + '/<int:issuance_id>', methods=['POST'])
@token_required
def edit_blood_issuance(current_user, issuance_id):
    issuance = BloodIssuance.query.get_or_404(issuance_id)

    try:
        # Validate required fields
        required_fields = ['patient_id', 'patient_name', 'blood_product_id',
                           'blood_type', 'component_type', 'quantity', 'issue_date']
        if not all(request.form.get(field) for field in required_fields):
            flash('Please fill in all required fields', 'danger')
            return redirect(request.url)

        # Update issuance
        issuance.patient_id = request.form['patient_id']
        issuance.patient_name = request.form['patient_name']
        issuance.patient_age = int(request.form.get('patient_age', 0)) if request.form.get('patient_age') else None
        issuance.patient_gender = request.form.get('patient_gender')
        issuance.blood_product_id = request.form['blood_product_id']
        issuance.blood_type = request.form['blood_type']
        issuance.component_type = request.form['component_type']
        issuance.quantity = int(request.form['quantity'])
        issuance.issue_date = datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date()
        issuance.status = request.form.get('status', 'Pending')
        issuance.doctor_id = request.form.get('doctor_id')
        issuance.doctor_name = request.form.get('doctor_name')
        issuance.transfusion_date = datetime.strptime(request.form['transfusion_date'],
                                                      '%Y-%m-%d').date() if request.form.get(
            'transfusion_date') else None
        issuance.issue_reason = request.form.get('issue_reason')
        issuance.remarks = request.form.get('remarks')
        issuance.updated_at = datetime.now()

        # Handle payment if patient exists
        patient_exists = check_patient_exists(request.form['patient_id'])
        if patient_exists:
            if request.form.get('payment_amount'):
                if issuance.payment_id:
                    # Update existing payment
                    payment = PatientPayment.query.get(issuance.payment_id)
                    payment.amount = float(request.form.get('payment_amount', 0))
                    payment.status = request.form.get('payment_status', 'unpaid')
                    if request.form.get('payment_date'):
                        payment.payment_date = datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date()
                    payment.remarks = request.form.get('payment_remarks', 'Blood product issuance')
                else:
                    # Create new payment
                    payment = create_payment_record(issuance, request.form)
                    issuance.payment_id = payment.id

        db.session.commit()
        flash('Issuance record updated successfully!', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating issuance record: {str(e)}', 'danger')

    return redirect(ADMIN + BLOOD_BANK_ISSUED)


@admin.route(BLOOD_BANK_DELETE_ISSUED + '/<int:issuance_id>', methods=['POST'])
@token_required
def delete_blood_issuance(current_user, issuance_id):
    issuance = BloodIssuance.query.get_or_404(issuance_id)

    try:
        issuance.is_deleted = True
        issuance.deleted_at = datetime.now()
        db.session.commit()
        flash('Issuance record archived successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error archiving issuance record: {str(e)}', 'danger')

    return redirect(ADMIN + BLOOD_BANK_ISSUED)


@admin.route(BLOOD_BANK_RESTORE_ISSUED + '/<int:issuance_id>', methods=['POST'])
@token_required
def restore_blood_issuance(current_user, issuance_id):
    issuance = BloodIssuance.query.get_or_404(issuance_id)

    try:
        issuance.is_deleted = False
        issuance.deleted_at = None
        db.session.commit()
        flash('Issuance record restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring issuance record: {str(e)}', 'danger')

    return redirect(ADMIN + BLOOD_BANK_ISSUED)
