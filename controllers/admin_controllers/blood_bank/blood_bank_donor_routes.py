from datetime import datetime, timedelta

from flask import render_template, request, redirect, flash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import BLOOD_BANK_DONOR, ADMIN, BLOOD_BANK_ADD_DONOR, BLOOD_BANK_EDIT_DONOR, \
    BLOOD_BANK_DELETE_DONOR, BLOOD_BANK_RESTORE_DONOR
from models.bloodModel import BloodDonor, BloodType
from models.patientModel import Patient
from models.userModel import User
from utils.config import db
from utils.create_new_patient import create_new_patient
from utils.update_blood_inventory import update_blood_inventory


@admin.route(BLOOD_BANK_DONOR, methods=['GET'], endpoint='blood_bank_donor')
def blood_bank_donor():
    donors = BloodDonor.query.filter_by(is_deleted=False).all()
    deleted_donors = BloodDonor.query.filter_by(is_deleted=True).all()
    return render_template("admin_templates/blood_bank/blood_donor.html",
                           donors=donors,
                           deleted_donors=deleted_donors,
                           datetime=datetime,
                           BloodType=BloodType,
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
        print(request.form)
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'blood_type', 'gender',
                           'patientAge', 'phone', 'email']
        if not all(request.form.get(field) for field in required_fields):
            flash('Please fill in all required fields', 'danger')
            return redirect(request.url)

        # If existing patient, verify patient exists
        if is_existing_patient and patient_id:
            patient = Patient.query.filter_by(patient_id=patient_id, is_deleted=False).first()
            if not patient:
                flash('Patient not found with the provided ID', 'danger')
                return redirect(request.url)

            patient_id = patient.id
        else:
            # Create new user and patient if checkbox is checked
            if request.form.get('create_patient') == 'on':
                # Check if email already exists
                existing_user = User.query.filter_by(email=request.form['email']).first()
                if existing_user:
                    flash('Email already exists in the system', 'danger')
                    return redirect(request.url)
                data = request.form

                patient = create_new_patient({
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'phone': data['phone'],
                    'age': data['patientAge'],
                    'gender': data.get('gender')
                })
                patient_id = patient.id

        next_eligible = datetime.strptime(request.form['last_donation'], '%Y-%m-%d').date() if request.form.get(
            'last_donation') else None + timedelta(days=56)
        # Create new donor
        new_donor = BloodDonor(
            patient_id=patient_id,
            donation_date=datetime.utcnow(),
            blood_type=BloodType(request.form['blood_type']),
            units_donated=float(request.form['units_donated']),
            status=request.form.get('status', 'Active'),
            last_donation=datetime.strptime(request.form['last_donation'], '%Y-%m-%d').date() if request.form.get(
                'last_donation') else None,
            next_eligible=next_eligible,
            emergency_contact_name=request.form.get('emergency_contact_name'),
            emergency_contact_phone=request.form.get('emergency_contact_phone'),
            emergency_contact_relation=request.form.get('emergency_contact_relation'),
            notes=request.form.get('notes'),

        )

        db.session.add(new_donor)
        db.session.commit()

        # Update inventory
        update_blood_inventory(
            blood_type=BloodType(new_donor.blood_type),
            units=float(new_donor.units_donated),
            donation_id=new_donor.id
        )

        flash(f'Donor added successfully!', 'success')

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
        donor.blood_type = BloodType(request.form['blood_type'])
        donor.units_donated = float(request.form['units_donated'])
        donor.status = request.form['status']
        donor.notes = request.form.get('notes')

        # Update dates
        last_donation = request.form.get('last_donation')
        if last_donation:
            donor.last_donation = datetime.strptime(last_donation, '%Y-%m-%d').date()
            donor.next_eligible = donor.last_donation + timedelta(days=56)

        # Emergency contact info
        donor.emergency_contact_name = request.form.get('emergency_contact_name')
        donor.emergency_contact_phone = request.form.get('emergency_contact_phone')
        donor.emergency_contact_relation = request.form.get('emergency_contact_relation')

        donor.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Donation record updated successfully!', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating donation: {str(e)}', 'danger')
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
