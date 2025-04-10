from flask import render_template, request, redirect, flash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import AMBULANCE_ADD_AMBULANCE, AMBULANCE_AMBULANCE_LIST, \
    AMBULANCE_AMBULANCE_CALL_LIST, AMBULANCE_ADD_DRIVER, AMBULANCE_DRIVER_LIST
from models.driverModel import Driver
from utils.config import db


@admin.route(AMBULANCE_ADD_AMBULANCE, methods=['GET'], endpoint='add-ambulance')
def addAmbulance():
    return render_template("admin_templates/ambulance/add-ambulance.html")


@admin.route(AMBULANCE_AMBULANCE_LIST, methods=['GET'], endpoint='ambulance-list')
def ambulanceList():
    return render_template("admin_templates/ambulance/ambulance-list.html")


@admin.route(AMBULANCE_AMBULANCE_CALL_LIST, methods=['GET'], endpoint='ambulance-call-list')
def ambulanceCallList():
    return render_template("admin_templates/ambulance/ambulance-call-list.html")


@admin.route(AMBULANCE_ADD_DRIVER, methods=['GET'], endpoint='add-driver')
def ambulanceAddDriver():
    return render_template("admin_templates/ambulance/add-driver.html")


@admin.route(AMBULANCE_DRIVER_LIST, methods=['GET'], endpoint='driver-list')
def ambulanceDriverList():
    return render_template("admin_templates/ambulance/driver-list.html")


@admin.route(AMBULANCE_ADD_DRIVER, methods=['POST'])
def add_driver():
    # Get form data
    name = request.form.get('name')
    license_number = request.form.get('license_number')
    contact = request.form.get('contact')
    address = request.form.get('address')

    # Validate required fields
    if not all([name, license_number, contact, address]):
        flash('All fields are required', 'danger')
        return redirect("/admin/" + AMBULANCE_ADD_DRIVER)

    # Check if license number already exists
    if Driver.query.filter_by(license_number=license_number).first():
        flash('Driver with this license number already exists', 'danger')
        return redirect("/admin/" + AMBULANCE_ADD_DRIVER)

    # Create new driver
    new_driver = Driver(
        name=name,
        license_number=license_number,
        contact=contact,
        address=address
    )

    try:
        db.session.add(new_driver)
        db.session.commit()
        flash('Driver added successfully!', 'success')
        return redirect("/admin/" + AMBULANCE_DRIVER_LIST)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding driver: {str(e)}', 'danger')
