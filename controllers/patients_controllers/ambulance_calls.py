# controllers/patient_controllers.py

from flask import render_template, redirect, url_for, flash, request
from sqlalchemy import desc

from controllers.constant.patientPathConstant import (
    PATIENT, PATIENT_AMBULANCE_CALLS, PATIENT_AMBULANCE_REQUESTS,
    PATIENT_AMBULANCE_REQUEST_NEW, PATIENT_AMBULANCE_REQUEST_VIEW
)
from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models import Patient
from models.ambulanceModel import AmbulanceCall, AmbulanceRequest, AmbulanceRequestStatus
from models.userModel import User  # Assuming User model
from models.userModel import UserRole  # Assuming UserRole Enum
from utils.config import db



@patients.route(PATIENT_AMBULANCE_CALLS, methods=['GET'], endpoint='ambulance_calls_list')
@token_required(allowed_roles=[UserRole.PATIENT.name, UserRole.ADMIN.name])  # Allow ADMIN for testing/support
def ambulance_calls_list(current_user):
    # Assuming current_user has an ID that can be mapped to a patient_id
    patient = Patient.query.filter_by(user_id=current_user).first()

    if not patient:
        flash("Patient profile not found.", "danger")
        return redirect(url_for('patient_dashboard'))  # Redirect to patient dashboard or home

    calls = AmbulanceCall.query.filter_by(patient_id=patient.id, is_deleted=False).order_by(
        desc(AmbulanceCall.call_time)).all()

    return render_template('patient_templates/ambulance/call_history.html',
                           calls=calls,
                           PATIENT=PATIENT)


@patients.route(PATIENT_AMBULANCE_REQUESTS, methods=['GET'], endpoint='ambulance_requests_list')
@token_required(allowed_roles=[UserRole.PATIENT.name, UserRole.ADMIN.name])
def ambulance_requests_list(current_user):
    requests = AmbulanceRequest.query.filter_by(requester_user_id=current_user).order_by(
        desc(AmbulanceRequest.request_time)).all()

    return render_template('patient_templates/ambulance/request_history.html',
                           requests=requests,
                           PATIENT=PATIENT,
                           AmbulanceRequestStatus=AmbulanceRequestStatus)  # Pass Enum for status display


@patients.route(PATIENT_AMBULANCE_REQUEST_NEW, methods=['GET', 'POST'], endpoint='ambulance_request_new')
@token_required(allowed_roles=[UserRole.PATIENT.name])
def ambulance_request_new(current_user):
    patient_id = get_patient_id_for_current_user(current_user.id)

    if not patient_id:
        flash("Patient profile not found. Cannot make a request.", "danger")
        return redirect(url_for('patient_dashboard'))

    if request.method == 'POST':
        pickup_location = request.form.get('pickup_location')
        emergency_description = request.form.get('emergency_description')
        # You might need to get patient_id from the current_user's linked patient profile

        if not pickup_location:
            flash("Pickup location is required.", "danger")
            return redirect(url_for('patient_bp.ambulance_request_new'))

        try:
            new_request = AmbulanceRequest(
                requester_user_id=current_user.id,
                patient_id=patient_id,  # Assuming current user is requesting for themselves or a default linked patient
                pickup_location=pickup_location,
                emergency_description=emergency_description,
                status=AmbulanceRequestStatus.PENDING  # Default status
            )
            db.session.add(new_request)
            db.session.commit()
            flash("Ambulance request submitted successfully! We will contact you shortly.", "success")
            return redirect(url_for('patient_bp.ambulance_requests_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting request: {str(e)}", "danger")
            # Log the error with traceback for debugging
            import traceback
            traceback.print_exc()

    return render_template('patient_templates/ambulance/request_new.html',
                           PATIENT=PATIENT)


@patients.route(PATIENT_AMBULANCE_REQUEST_VIEW + '/<int:request_id>', methods=['GET'],
                endpoint='ambulance_request_view')
@token_required(allowed_roles=[UserRole.PATIENT.name])
def ambulance_request_view(current_user, request_id):
    # Ensure the request belongs to the current user for security
    patient_request = AmbulanceRequest.query.filter_by(
        id=request_id,
        requester_user_id=current_user.id
    ).first_or_404()

    return render_template('patient_templates/ambulance/request_detail.html',
                           patient_request=patient_request,
                           PATIENT=PATIENT,
                           AmbulanceRequestStatus=AmbulanceRequestStatus)
