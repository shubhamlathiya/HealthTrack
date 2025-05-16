from datetime import datetime, timedelta

from flask import render_template, flash, redirect, request, jsonify
from sqlalchemy import func, or_

from controllers.constant.patientPathConstant import PATIENT_BLOOD_REQUEST, PATIENT_MY_REQUESTS, PATIENT, \
    PATIENT_PAY_REQUEST, PAYMENT_CONFIRMATION
from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models.bloodModel import BloodRequest, BloodDonor
from models.patientModel import Patient
from models.userModel import UserRole
from utils.config import db


@patients.route(PATIENT_BLOOD_REQUEST, methods=['GET', 'POST'], endpoint="request_blood")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def request_blood(current_user):
    if request.method == 'POST':
        try:
            data = request.form

            # Validate required fields
            required_fields = ['blood_type', 'component_type', 'quantity', 'required_date', 'reason']
            if not all(data.get(field) for field in required_fields):
                flash('Please fill all required fields', 'danger')
                return redirect(request.url)

            # Get patient details
            patient = Patient.query.filter_by(user_id=current_user).first()
            if not patient:
                flash('Patient profile not found', 'danger')
                return redirect("/")

            # Create blood request
            new_request = BloodRequest(
                patient_id=patient.patient_id,
                patient_name=f"{patient.first_name} {patient.last_name}",
                blood_type=data['blood_type'],
                component_type=data['component_type'],
                quantity=int(data['quantity']),
                required_date=datetime.strptime(data['required_date'], '%Y-%m-%d').date(),
                reason=data['reason'],
                status='Pending'
            )

            # Calculate cost and generate request ID
            new_request.calculate_cost()
            new_request.generate_request_id()

            db.session.add(new_request)
            db.session.flush()  # Generate ID for relationships

            # Try to automatically approve if stock is available
            if new_request.approve_request(approved_by='System'):
                # If auto-approved, set status to Payment Pending
                new_request.status = 'Payment Pending'
                flash(
                    f'Blood request approved! Your request ID: {new_request.request_id}. Amount: ₹{new_request.payment_amount}',
                    'success')
            else:
                # Not enough stock, keep as pending
                flash(
                    f'Blood request submitted! Your request ID: {new_request.request_id}. Waiting for stock availability.',
                    'info')

            db.session.commit()
            return redirect(PATIENT + PATIENT_MY_REQUESTS)

        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting request: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request - show form
    patient = Patient.query.filter_by(user_id=current_user).first()
    if not patient:
        flash('Patient profile not found', 'danger')
        return redirect(PATIENT + PATIENT_MY_REQUESTS)

    return render_template('patient_templates/blood_donor/blood_request_form.html',
                           blood_types=BloodDonor.BLOOD_TYPES,
                           patient=patient,
                           datetime=datetime,
                           component_types=['Whole Blood', 'Red Blood Cells', 'Plasma', 'Platelets', 'Cryoprecipitate'],
                           min_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))



@patients.route('/api/blood-availability', methods=['POST'])
def blood_availability():
    # Get JSON data from request
    data = request.get_json()
    print(data)
    # Validate required fields
    if not data or 'blood_type' not in data or 'component_type' not in data:
        return jsonify({
            'success': False,
            'message': 'Missing required fields in request'
        }), 400

    blood_type = data['blood_type'].strip().upper()
    component_type = data['component_type'].strip()
    requested_quantity = data.get('quantity', 1)  # Default to 1 if not provided

    # Fix common formatting issues
    blood_type = blood_type.replace(' ', '+')

    # Validate blood type
    valid_blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    if blood_type not in valid_blood_types:
        return jsonify({
            'success': False,
            'message': f'Invalid blood type: {blood_type}',
            'valid_blood_types': valid_blood_types
        }), 400

    # Validate component type
    valid_components = ['Whole Blood', 'Red Blood Cells', 'Plasma', 'Platelets', 'Cryoprecipitate']
    if component_type not in valid_components:
        return jsonify({
            'success': False,
            'message': f'Invalid component type: {component_type}',
            'valid_components': valid_components
        }), 400

    # Calculate available stock (same as before)
    total_quantity = db.session.query(
        func.sum(BloodProduct.quantity)
    ).filter(
        BloodProduct.blood_type == blood_type,
        BloodProduct.component_type == component_type,
        BloodProduct.is_deleted == False,
        BloodProduct.expiry_date >= datetime.now().date(),
        or_(BloodProduct.status == 'Fresh', BloodProduct.status == 'Near Expiry')
    ).scalar() or 0

    available_quantity = max(0, total_quantity)

    return jsonify({
        'success': True,
        'blood_type': blood_type,
        'component_type': component_type,
        'is_available': available_quantity >= requested_quantity,
        'quantity': available_quantity,
        'requested_quantity': requested_quantity,
        'total_inventory': total_quantity,
        'timestamp': datetime.now().isoformat()
    })


@patients.route(PATIENT_MY_REQUESTS, methods=['GET'], endpoint="my_blood_requests")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def my_blood_requests(current_user):
    patient = Patient.query.filter_by(user_id=current_user).first()
    if not patient:
        flash('Patient profile not found', 'danger')
        return redirect(PATIENT + PATIENT_MY_REQUESTS)

    requests = BloodRequest.query.filter_by(patient_id=patient.patient_id) \
        .order_by(BloodRequest.request_date.desc()).all()

    return render_template('patient_templates/blood_donor/my_blood_requests.html',
                           requests=requests)


@patients.route(PATIENT_PAY_REQUEST, methods=['GET', 'POST'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def pay_blood_request(current_user, request_id):
    patient = Patient.query.filter_by(user_id=current_user).first()
    if not patient:
        flash('Patient profile not found', 'danger')
        return redirect(PATIENT + PATIENT_MY_REQUESTS)

    # Get the blood request
    blood_request = BloodRequest.query.filter_by(
        request_id=request_id,
        patient_id=patient.patient_id
    ).first_or_404()

    # Validate request can be paid
    if blood_request.status != 'Payment Pending':
        flash('This request cannot be paid at this time', 'danger')
        return redirect(PATIENT + PATIENT_MY_REQUESTS)

    if request.method == 'POST':
        try:
            payment_method = request.form.get('payment_method', 'Cash')

            # Complete the request (marks as paid and updates inventory)
            if blood_request.complete_request(payment_method):
                db.session.commit()

                # Send confirmation
                send_confirmation_email(
                    current_user,
                    blood_request,
                    blood_request.issuances[0] if blood_request.issuances else None
                )

                flash('Payment processed successfully! Your blood has been reserved.', 'success')
                return redirect(PATIENT + PATIENT_MY_REQUESTS)
            else:
                flash('Could not process payment. Please try again.', 'danger')
                return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            flash(f'Error processing payment: {str(e)}', 'danger')
            return redirect(request.url)

    # GET request - show payment page
    return render_template('patient_templates/payments/payment_confirm.html',
                           request=blood_request)


@patients.route(PAYMENT_CONFIRMATION, methods=['GET'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def payment_confirmation(current_user, request_id):
    patient = Patient.query.filter_by(user_id=current_user).first()
    if not patient:
        flash('Patient profile not found', 'danger')
        return redirect(PATIENT + PATIENT_MY_REQUESTS)

    blood_request = BloodRequest.query.filter_by(
        request_id=request_id,
        patient_id=patient.patient_id
    ).first_or_404()

    if blood_request.payment_status != 'Paid':
        flash('Payment not completed yet', 'warning')
        return redirect(PATIENT + PATIENT_MY_REQUESTS)

    return render_template('patient_templates/payments/payment_success.html',
                           request=blood_request)


def send_confirmation_email(user, blood_request, issuance):
    subject = f"Blood Request Confirmation - {blood_request.request_id}"
    body = f"""
    Dear {user.first_name},

    Your blood request has been successfully processed.

    Request Details:
    - Request ID: {blood_request.request_id}
    - Blood Type: {blood_request.blood_type}
    - Component: {blood_request.component_type}
    - Quantity: {blood_request.quantity} units
    - Amount Paid: ₹{blood_request.payment_amount}

    Issuance Details:
    - Issuance ID: {issuance.issue_id if issuance else 'N/A'}
    - Collection Location: {issuance.blood_product.storage_location if issuance else 'N/A'}

    Please bring this confirmation and your ID when collecting the blood.
    """
    # send_email(subject, user.email, body)