from datetime import datetime

from flask import render_template, request, redirect, flash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import AMBULANCE_AMBULANCE_CALL_LIST, AMBULANCE_AMBULANCE_ADD_CALL, \
    AMBULANCE_AMBULANCE_EDIT_CALL, AMBULANCE_AMBULANCE_DELETE_CALL, AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL, \
    AMBULANCE_AMBULANCE_RESTORE_CALL, ADMIN
from models.ambulanceModel import AmbulanceCall, Ambulance, Driver
from utils.config import db


@admin.route(AMBULANCE_AMBULANCE_CALL_LIST, methods=['GET'], endpoint='ambulance-call-list')
def ambulance_call_list():
    calls = AmbulanceCall.query.filter_by(is_deleted=False).order_by(AmbulanceCall.call_time.desc()).all()
    ambulances = Ambulance.query.filter_by(is_active=True, is_available=True).all()
    drivers = Driver.query.filter_by(is_active=True).all()
    deleted_calls = AmbulanceCall.query.filter_by(is_deleted=True).all()
    return render_template("admin_templates/ambulance/ambulance-call-list.html",
                           calls=calls,
                           ambulances=ambulances,
                           drivers=drivers,
                           deleted_calls=deleted_calls,
                           ADMIN=ADMIN,
                           AMBULANCE_AMBULANCE_ADD_CALL=AMBULANCE_AMBULANCE_ADD_CALL,
                           AMBULANCE_AMBULANCE_EDIT_CALL=AMBULANCE_AMBULANCE_EDIT_CALL,
                           AMBULANCE_AMBULANCE_DELETE_CALL=AMBULANCE_AMBULANCE_DELETE_CALL,
                           AMBULANCE_AMBULANCE_RESTORE_CALL=AMBULANCE_AMBULANCE_RESTORE_CALL,
                           AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL=AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL
                           )


@admin.route(AMBULANCE_AMBULANCE_ADD_CALL, methods=['POST'], endpoint='add-ambulance-call')
def add_ambulance_call():
    try:
        # Generate call number (AMB-YYYY-MMDD-NNN)
        today = datetime.now()
        last_call = AmbulanceCall.query.order_by(AmbulanceCall.id.desc()).first()
        sequence_num = 1 if not last_call else last_call.id + 1
        call_number = f"AMB-{today.year}-{today.month:02d}{today.day:02d}-{sequence_num:03d}"

        new_call = AmbulanceCall(
            call_number=request.form.get('call_number'),
            patient_name=request.form.get('patient_name'),
            patient_age=int(request.form.get('patient_age')),
            patient_gender=request.form.get('patient_gender'),
            pickup_location=request.form.get('pickup_location'),
            destination=request.form.get('destination'),
            call_time=datetime.strptime(request.form.get('call_time'), '%Y-%m-%dT%H:%M'),
            status='Pending',
            notes=request.form.get('notes'),
            ambulance_id=request.form.get('ambulance_id'),
            driver_id=request.form.get('driver_id')
        )

        db.session.add(new_call)
        db.session.commit()
        flash('Ambulance call added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding ambulance call: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route(AMBULANCE_AMBULANCE_EDIT_CALL + '/<int:id>', methods=['POST'], endpoint='edit-ambulance-call')
def edit_ambulance_call(id):
    call = AmbulanceCall.query.get_or_404(id)
    try:
        call.patient_name = request.form.get('patient_name')
        call.patient_age = int(request.form.get('patient_age'))
        call.patient_gender = request.form.get('patient_gender')
        call.pickup_location = request.form.get('pickup_location')
        call.destination = request.form.get('destination')
        call.call_time = datetime.strptime(request.form.get('call_time'), '%Y-%m-%dT%H:%M')
        call.status = request.form.get('status')
        call.notes = request.form.get('notes')
        call.ambulance_id = request.form.get('ambulance_id')
        call.driver_id = request.form.get('driver_id')

        # Update timestamps based on status
        if call.status == 'Dispatched' and not call.dispatch_time:
            call.dispatch_time = datetime.utcnow()
        elif call.status == 'In Progress' and not call.arrival_time:
            call.arrival_time = datetime.utcnow()
        elif call.status == 'Completed' and not call.completion_time:
            call.completion_time = datetime.utcnow()
            # Calculate charges if distance is provided
            if request.form.get('distance'):
                call.distance = float(request.form.get('distance'))
                ambulance = Ambulance.query.get(call.ambulance_id)
                if ambulance:
                    call.charges = ambulance.base_rate + (ambulance.per_km_rate * call.distance)

        db.session.commit()
        flash('Ambulance call updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating ambulance call: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route(AMBULANCE_AMBULANCE_DELETE_CALL + '/<int:id>', methods=['POST'], endpoint='delete-ambulance-call')
def delete_ambulance_call(id):
    call = AmbulanceCall.query.get_or_404(id)
    try:
        call.deleted_at = datetime.utcnow()
        call.is_deleted = True
        db.session.commit()
        db.session.commit()
        flash('Ambulance call deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ambulance call: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route(AMBULANCE_AMBULANCE_RESTORE_CALL + '/<int:id>', methods=['POST'], endpoint='restore-ambulance-call')
def restore_ambulance_call(id):
    call = AmbulanceCall.query.get_or_404(id)
    try:
        call.deleted_at = None
        call.is_deleted = False
        db.session.commit()
        db.session.commit()
        flash('Ambulance call Restore successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error Restore ambulance call: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route(AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL + '/<int:id>', methods=['POST'], endpoint='update-call-status')
def update_call_status(id):
    call = AmbulanceCall.query.get_or_404(id)
    new_status = request.form.get('status')

    try:
        call.status = new_status

        # Update timestamps based on status
        if new_status == 'Dispatched' and not call.dispatch_time:
            call.dispatch_time = datetime.utcnow()
            # Mark ambulance as unavailable
            if call.ambulance:
                call.ambulance.is_available = False
        elif new_status == 'In Progress' and not call.arrival_time:
            call.arrival_time = datetime.utcnow()
        elif new_status == 'Completed' and not call.completion_time:
            call.completion_time = datetime.utcnow()
            # Mark ambulance as available
            if call.ambulance:
                call.ambulance.is_available = True
            # Calculate charges if distance is provided
            if request.form.get('distance'):
                call.distance = float(request.form.get('distance'))
                if call.ambulance:
                    call.charges = call.ambulance.base_rate + (call.ambulance.per_km_rate * call.distance)
        elif new_status == 'Cancelled':
            # Mark ambulance as available if it was assigned
            if call.ambulance:
                call.ambulance.is_available = True

        db.session.commit()
        flash(f'Call status updated to {new_status}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating call status: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)
