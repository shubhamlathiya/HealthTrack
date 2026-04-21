# controllers/patients_controllers/ambulance_calls.py

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
from models.userModel import User, UserRole
from utils.config import db


@patients.route(PATIENT_AMBULANCE_CALLS, methods=['GET'], endpoint='ambulance_calls_list')
@token_required(allowed_roles=[UserRole.PATIENT.name, UserRole.ADMIN.name])
def ambulance_calls_list(current_user):
    patient = Patient.query.filter_by(user_id=current_user).first()

    if not patient:
        flash("Patient profile not found.", "danger")
        return redirect(url_for('patient_dashboard'))

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
                           AmbulanceRequestStatus=AmbulanceRequestStatus,
                           PATIENT_AMBULANCE_REQUEST_NEW = PATIENT_AMBULANCE_REQUEST_NEW)


@patients.route(PATIENT_AMBULANCE_REQUEST_NEW, methods=['GET', 'POST'], endpoint='ambulance_request_new1')
@token_required(allowed_roles=[UserRole.PATIENT.name])
def ambulance_request_new(current_user):
    # Get the patient profile linked to this user
    patient = Patient.query.filter_by(user_id=current_user).first()

    if not patient:
        flash("Patient profile not found. Cannot make a request.", "danger")
        return redirect(url_for('patient_dashboard'))

    if request.method == 'POST':
        pickup_location = request.form.get('pickup_location')
        emergency_description = request.form.get('emergency_description')

        if not pickup_location:
            flash("Pickup location is required.", "danger")
            return redirect(url_for('patients.ambulance_request_new'))  # Fixed: changed to patients

        try:
            new_request = AmbulanceRequest(
                requester_user_id=current_user.id,
                patient_id=patient.id,  # Fixed: use patient.id instead of patient_id variable
                pickup_location=pickup_location,
                emergency_description=emergency_description,
                status=AmbulanceRequestStatus.PENDING
            )
            db.session.add(new_request)
            db.session.commit()
            flash("Ambulance request submitted successfully! We will contact you shortly.", "success")
            return redirect(url_for('patients.ambulance_requests_list'))  # Fixed: changed to patients
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting request: {str(e)}", "danger")
            import traceback
            traceback.print_exc()

    return render_template('patient_templates/ambulance/request_new.html',
                           PATIENT=PATIENT)


@patients.route(PATIENT_AMBULANCE_REQUEST_VIEW + '/<int:request_id>', methods=['GET'],
                endpoint='ambulance_request_view')
@token_required(allowed_roles=[UserRole.PATIENT.name])
def ambulance_request_view(current_user, request_id):
    patient_request = AmbulanceRequest.query.filter_by(
        id=request_id,
        requester_user_id=current_user.id
    ).first_or_404()

    return render_template('patient_templates/ambulance/request_detail.html',
                           patient_request=patient_request,
                           PATIENT=PATIENT,
                           AmbulanceRequestStatus=AmbulanceRequestStatus)