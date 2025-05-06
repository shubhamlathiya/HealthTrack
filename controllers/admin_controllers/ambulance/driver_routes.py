# Driver Routes
from datetime import datetime

from flask import redirect, request, render_template, flash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import AMBULANCE_DRIVER_LIST, \
    AMBULANCE_ADD_DRIVER, ADMIN, AMBULANCE_EDIT_DRIVER, AMBULANCE_DELETE_DRIVER, AMBULANCE_RESTORE_DRIVER, \
    AMBULANCE_TOGGLE_STATUS_DRIVER
from models.ambulanceModel import Driver
from utils.config import db


@admin.route(AMBULANCE_DRIVER_LIST, methods=['GET'], endpoint='driver-list')
def driver_list():
    drivers = Driver.query.filter_by(deleted_at=None).all()
    deleted_drivers = Driver.query.filter_by(is_deleted=True).all()
    return render_template("admin_templates/ambulance/driver-list.html",
                           drivers=drivers,
                           deleted_drivers=deleted_drivers,
                           ADMIN=ADMIN,
                           AMBULANCE_ADD_DRIVER=AMBULANCE_ADD_DRIVER,
                           AMBULANCE_EDIT_DRIVER=AMBULANCE_EDIT_DRIVER,
                           AMBULANCE_DELETE_DRIVER=AMBULANCE_DELETE_DRIVER,
                           AMBULANCE_RESTORE_DRIVER=AMBULANCE_RESTORE_DRIVER,
                           AMBULANCE_TOGGLE_STATUS_DRIVER=AMBULANCE_TOGGLE_STATUS_DRIVER)


@admin.route(AMBULANCE_ADD_DRIVER, methods=['POST'], endpoint='add-driver')
def driver_operations():
    name = request.form.get('name')
    license_number = request.form.get('license_number')
    contact = request.form.get('contact')
    address = request.form.get('address')
    date_of_birth = request.form.get('date_of_birth')
    gender = request.form.get('gender')

    if not all([name, license_number, contact, address]):
        flash('All required fields must be filled', 'danger')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

    if Driver.query.filter_by(license_number=license_number).first():
        flash('Driver with this license number already exists', 'danger')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

    new_driver = Driver(
        name=name,
        license_number=license_number,
        contact=contact,
        address=address,
        date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d') if date_of_birth else None,
        gender=gender
    )

    try:
        db.session.add(new_driver)
        db.session.commit()
        flash('Driver added successfully!', 'success')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding driver: {str(e)}', 'danger')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


@admin.route(AMBULANCE_EDIT_DRIVER + '/<int:id>', methods=['POST'], endpoint='edit-driver')
def edit_driver(id):
    driver = Driver.query.get_or_404(id)

    driver.name = request.form.get('name')
    driver.license_number = request.form.get('license_number')
    driver.contact = request.form.get('contact')
    driver.address = request.form.get('address')
    driver.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d') if request.form.get(
        'date_of_birth') else None
    driver.gender = request.form.get('gender')
    driver.is_active = request.form.get('is_active') == 'on'

    try:
        db.session.commit()
        flash('Driver updated successfully!', 'success')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating driver: {str(e)}', 'danger')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


@admin.route(AMBULANCE_DELETE_DRIVER + '/<int:id>', methods=['POST'], endpoint='delete-driver')
def delete_driver(id):
    driver = Driver.query.get_or_404(id)
    try:
        driver.deleted_at = datetime.utcnow()
        driver.is_deleted = True
        db.session.commit()
        flash('Driver deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting driver: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


@admin.route(AMBULANCE_RESTORE_DRIVER + '/<int:id>', methods=['POST'], endpoint='restore-driver')
def restore_driver(id):
    driver = Driver.query.get_or_404(id)
    try:
        driver.deleted_at = None
        driver.is_deleted = False
        db.session.commit()
        flash('Driver restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring driver: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


@admin.route(AMBULANCE_TOGGLE_STATUS_DRIVER + '/<int:id>', methods=['POST'], endpoint='toggle-driver-status')
def toggle_driver_status(id):
    driver = Driver.query.get_or_404(id)
    try:
        driver.is_active = not driver.is_active
        db.session.commit()
        status = "activated" if driver.is_active else "deactivated"
        flash(f'Driver {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling driver status: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)
