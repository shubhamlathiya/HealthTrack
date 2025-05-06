from datetime import datetime

from flask import render_template, request, redirect, flash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import AMBULANCE_ADD_AMBULANCE, AMBULANCE_AMBULANCE_LIST, \
    ADMIN, AMBULANCE_EDIT_AMBULANCE, AMBULANCE_DELETE_AMBULANCE, AMBULANCE_RESTORE_AMBULANCE, \
    AMBULANCE_TOGGLE_STATUS_AMBULANCE
from models.ambulanceModel import Ambulance, Driver
from utils.config import db


@admin.route(AMBULANCE_AMBULANCE_LIST, methods=['GET'], endpoint='ambulance-list')
def ambulance_list():
    ambulances = Ambulance.query.filter_by(deleted_at=None).all()
    drivers = Driver.query.filter_by(is_active=True, deleted_at=None).all()
    deleted_ambulances = Ambulance.query.filter_by(is_deleted=True).all()
    return render_template("admin_templates/ambulance/ambulance-list.html",
                           ambulances=ambulances,
                           current_year=datetime.today().year,
                           drivers=drivers,
                           deleted_ambulances=deleted_ambulances,
                           ADMIN=ADMIN,
                           AMBULANCE_ADD_AMBULANCE=AMBULANCE_ADD_AMBULANCE,
                           AMBULANCE_EDIT_AMBULANCE=AMBULANCE_EDIT_AMBULANCE,
                           AMBULANCE_DELETE_AMBULANCE=AMBULANCE_DELETE_AMBULANCE,
                           AMBULANCE_RESTORE_AMBULANCE=AMBULANCE_RESTORE_AMBULANCE,
                           AMBULANCE_TOGGLE_STATUS_AMBULANCE=AMBULANCE_TOGGLE_STATUS_AMBULANCE
                           )


@admin.route(AMBULANCE_ADD_AMBULANCE, methods=['POST'], endpoint='add-ambulance')
def ambulance_operations():
    # Add new ambulance
    vehicle_number = request.form.get('vehicle_number')
    vehicle_name = request.form.get('vehicle_name')
    year_made = request.form.get('year_made')
    vehicle_type = request.form.get('vehicle_type')
    base_rate = float(request.form.get('base_rate', 0))
    per_km_rate = float(request.form.get('per_km_rate', 0))
    driver_id = request.form.get('driver_id')

    if not all([vehicle_number, vehicle_name, year_made, vehicle_type]):
        flash('All required fields must be filled', 'danger')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)

    if Ambulance.query.filter_by(vehicle_number=vehicle_number).first():
        flash('Ambulance with this vehicle number already exists', 'danger')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)

    new_ambulance = Ambulance(
        vehicle_number=vehicle_number,
        vehicle_name=vehicle_name,
        year_made=year_made,
        vehicle_type=vehicle_type,
        base_rate=base_rate,
        per_km_rate=per_km_rate,
        driver_id=driver_id if driver_id else None
    )

    try:
        db.session.add(new_ambulance)
        db.session.commit()
        flash('Ambulance added successfully!', 'success')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding ambulance: {str(e)}', 'danger')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)


@admin.route(AMBULANCE_EDIT_AMBULANCE + '/<int:id>', methods=['POST'], endpoint='edit-ambulance')
def edit_ambulance(id):
    ambulance = Ambulance.query.get_or_404(id)

    ambulance.vehicle_number = request.form.get('vehicle_number')
    ambulance.vehicle_name = request.form.get('vehicle_name')
    ambulance.year_made = request.form.get('year_made')
    ambulance.vehicle_type = request.form.get('vehicle_type')
    ambulance.base_rate = float(request.form.get('base_rate', 0))
    ambulance.per_km_rate = float(request.form.get('per_km_rate', 0))
    ambulance.driver_id = request.form.get('driver_id')
    ambulance.is_available = request.form.get('is_available') == 'on'
    ambulance.is_active = request.form.get('is_active') == 'on'

    try:
        db.session.commit()
        flash('Ambulance updated successfully!', 'success')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating ambulance: {str(e)}', 'danger')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)


@admin.route(AMBULANCE_DELETE_AMBULANCE + '/<int:id>', methods=['POST'], endpoint='delete-ambulance')
def delete_ambulance(id):
    ambulance = Ambulance.query.get_or_404(id)
    try:
        ambulance.deleted_at = datetime.utcnow()
        ambulance.is_deleted = True
        db.session.commit()
        flash('Ambulance deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ambulance: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)


@admin.route(AMBULANCE_RESTORE_AMBULANCE + '/<int:id>', methods=['POST'], endpoint='restore-ambulance')
def restore_ambulance(id):
    ambulance = Ambulance.query.get_or_404(id)
    try:
        ambulance.deleted_at = None
        ambulance.is_deleted = False
        db.session.commit()
        flash('Ambulance restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring ambulance: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)


@admin.route(AMBULANCE_TOGGLE_STATUS_AMBULANCE + '/<int:id>', methods=['POST'], endpoint='toggle-ambulance-status')
def toggle_ambulance_status(id):
    ambulance = Ambulance.query.get_or_404(id)
    try:
        ambulance.is_active = not ambulance.is_active
        db.session.commit()
        status = "activated" if ambulance.is_active else "deactivated"
        flash(f'Ambulance {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling ambulance status: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_LIST)
