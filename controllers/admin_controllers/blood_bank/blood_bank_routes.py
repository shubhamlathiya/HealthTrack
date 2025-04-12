from datetime import datetime
import os
from flask import render_template, request, flash, redirect
from werkzeug.utils import secure_filename

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import BLOOD_BANK_DONOR, BLOOD_BANK_STOCK, BLOOD_BANK_ISSUED, \
    BLOOD_BANK_ADD_DONOR
from models.bloodDonorModel import BloodDonor
from utils.config import db

UPLOAD_FOLDER = 'uploads/blood_bank'  # Base folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin.route(BLOOD_BANK_DONOR, methods=['GET'], endpoint='blood_bank_donor')
def blood_bank_donor():
    # Query all blood donors from the database
    donors = BloodDonor.query.order_by(BloodDonor.registration_date.desc()).all()

    return render_template(
        "admin_templates/blood_bank/blood_donor.html",
        donors=donors
    )


@admin.route(BLOOD_BANK_ADD_DONOR, methods=['GET'], endpoint='blood_bank_add_donor')
def blood_bank_add_donor():
    return render_template("admin_templates/blood_bank/add_blood_donor.html", blood_types=BloodDonor.BLOOD_TYPES)


@admin.route(BLOOD_BANK_ADD_DONOR, methods=['POST'])
def add_donor():
    # Get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    blood_type = request.form.get('blood_type')
    gender = request.form.get('gender')
    date_of_birth = request.form.get('date_of_birth')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    status = request.form.get('status')
    last_donation = request.form.get('last_donation')
    medical_history = request.form.get('medical_history')
    emergency_contact_name = request.form.get('emergency_contact_name')
    emergency_contact_phone = request.form.get('emergency_contact_phone')
    emergency_contact_relation = request.form.get('emergency_contact_relation')
    notes = request.form.get('notes')

    # Handle file upload
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            image_path = os.path.join(UPLOAD_FOLDER, filename)

    # Validate required fields
    required_fields = [first_name, last_name, blood_type, gender, date_of_birth, phone]
    if not all(required_fields):
        flash('Please fill all required fields', 'danger')
        return redirect("/admin/" + BLOOD_BANK_ADD_DONOR)

    # Create new donor
    new_donor = BloodDonor(
        first_name=first_name,
        last_name=last_name,
        blood_type=blood_type,
        gender=gender,
        date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date(),
        phone=phone,
        email=email,
        address=address,
        status=status,
        medical_history=medical_history,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_phone=emergency_contact_phone,
        emergency_contact_relation=emergency_contact_relation,
        notes=notes,
        image_path=image_path
    )

    # Set last donation and calculate next eligible date
    if last_donation:
        new_donor.last_donation = datetime.strptime(last_donation, '%Y-%m-%d').date()
        new_donor.calculate_next_eligible()

    try:
        db.session.add(new_donor)
        db.session.commit()
        flash('Donor added successfully!', 'success')
        return redirect("/admin/" + BLOOD_BANK_ADD_DONOR)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding donor: {str(e)}', 'danger')
        return redirect("/admin/" + BLOOD_BANK_ADD_DONOR)


@admin.route(BLOOD_BANK_STOCK, methods=['GET'], endpoint='blood_bank_stock')
def blood_bank_stock():
    return render_template("admin_templates/blood_bank/blood_stock.html")


@admin.route(BLOOD_BANK_ISSUED, methods=['GET'], endpoint='blood_bank_issued')
def blood_bank_issued():
    return render_template("admin_templates/blood_bank/blood_issued.html")
