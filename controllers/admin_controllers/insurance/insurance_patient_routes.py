import os
from datetime import date

from flask import render_template, request, flash, redirect
from sqlalchemy import func, cast, Date

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import INSURANCE_PATIENT, ADMIN, \
    INSURANCE_PATIENT_ADD_RECORDS, INSURANCE_PATIENT_RESTORE_RECORDS, INSURANCE_PATIENT_DELETE_RECORDS, \
    INSURANCE_PATIENT_EDIT_RECORDS
from middleware.auth_middleware import token_required
from models.insuranceProviderModel import (
    InsuranceProvider,
    InsuranceRecord
)
from models.patientModel import Patient
from utils.config import db

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/claims'
APPEAL_FOLDER = 'static/uploads/appeals'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(APPEAL_FOLDER, exist_ok=True)

# Claim status constants
CLAIM_STATUS = {
    'PENDING': 'Pending',
    'APPROVED': 'Approved',
    'REJECTED': 'Rejected',
    'APPEAL': 'Appeal Pending'
}

from datetime import datetime, timedelta


@admin.route(INSURANCE_PATIENT, methods=['GET'], endpoint='insurance_patient')
@token_required
def insurance_patient(current_user):
    try:
        today = date.today()
        next_30_days = today + timedelta(days=30)

        # Get all insurance records (excluding deleted), ordered by coverage_end desc
        insurance_records = db.session.query(InsuranceRecord). \
            join(InsuranceProvider, InsuranceRecord.insurance_provider_id == InsuranceProvider.id, isouter=True). \
            filter(InsuranceRecord.is_deleted == False). \
            order_by(InsuranceRecord.coverage_end.desc()).all()

        deleted_records = db.session.query(InsuranceRecord). \
            join(InsuranceProvider, InsuranceRecord.insurance_provider_id == InsuranceProvider.id, isouter=True). \
            filter(InsuranceRecord.is_deleted == True). \
            order_by(InsuranceRecord.coverage_end.desc()).all()

        # Count total (excluding deleted)
        total_count = db.session.query(func.count()).filter(InsuranceRecord.is_deleted == False).scalar()

        # Count active
        active_count = db.session.query(func.count()).filter(
            InsuranceRecord.status == 'Active',
            InsuranceRecord.is_deleted == False
        ).scalar()

        # Count expiring soon (next 30 days)
        expiring_soon_count = db.session.query(func.count()).filter(
            cast(InsuranceRecord.coverage_end, Date).between(today, next_30_days),
            InsuranceRecord.is_deleted == False
        ).scalar()

        # Count expired
        expired_count = db.session.query(func.count()).filter(
            cast(InsuranceRecord.coverage_end, Date) < today,
            InsuranceRecord.is_deleted == False
        ).scalar()

        # Load active insurance providers
        insurance_providers = db.session.query(InsuranceProvider).filter(
            InsuranceProvider.is_deleted == False,
            InsuranceProvider.status == 'Active'
        ).order_by(InsuranceProvider.name).all()

        return render_template("admin_templates/insurance/patient_insurance.html",
                               insurance_records=insurance_records,
                               total_count=total_count,
                               active_count=active_count,
                               expiring_soon_count=expiring_soon_count,
                               expired_count=expired_count,
                               providers=insurance_providers,
                               deleted_records=deleted_records
                               )

    except Exception as e:
        print(f"Error loading insurance records: {e}")
        return render_template("admin_templates/insurance/patient_insurance.html",
                               insurance_records=[],
                               total_count=0,
                               active_count=0,
                               expiring_soon_count=0,
                               expired_count=0,
                               insurance_providers=[])


@admin.route(INSURANCE_PATIENT_ADD_RECORDS, methods=['POST'], endpoint="insurance_patient_add_records")
@token_required
def add_record(current_user):
    try:
        print(request.form)

        # 1. Extract from form
        patient_id = request.form['patient_id']
        patient_name = request.form['patient_name']
        insurance_provider_id = int(request.form['insurance_provider_id'])

        patient = Patient.query.filter_by(patient_id=patient_id).first()
        # 2. Auto-generate IDs
        now_str = datetime.now().strftime('%Y%m%d%H%M%S')
        insurance_id = f"INS{now_str}"
        policy_number = f"POL{now_str}"  # Or keep request.form['policy_number'] if you want manual entry

        # 3. Create new InsuranceRecord
        new_record = InsuranceRecord(
            insurance_id=insurance_id,
            patient_id=patient_id,
            patient_name=patient_name,
            policy_number=policy_number,  # Or use request.form['policy_number'] if preferred
            policy_type=request.form['policy_type'],
            coverage_start=datetime.strptime(request.form['coverage_start'], '%Y-%m-%d').date(),
            coverage_end=datetime.strptime(request.form['coverage_end'], '%Y-%m-%d').date(),
            coverage_amount=float(request.form['coverage_amount']),
            copayment=float(request.form.get('copayment', 0)),
            status=request.form['status'],
            remarks=request.form.get('remarks'),
            insurance_provider_id=insurance_provider_id,
            patient_user_id=patient.user_id
        )

        # 4. Save to DB
        db.session.add(new_record)
        db.session.commit()
        flash('Insurance record added successfully', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding insurance record: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_PATIENT)


@admin.route(INSURANCE_PATIENT_EDIT_RECORDS + '/<int:record_id>', methods=['POST'], endpoint='insurance_record_edit')
@token_required
def edit_record(current_user, record_id):
    try:
        # Get the existing record
        record = InsuranceRecord.query.get_or_404(record_id)

        # Update record fields from form data
        record.patient_id = request.form['patient_id']
        record.patient_name = request.form['patient_name']
        record.insurance_provider_id = int(request.form['insurance_provider_id'])
        record.policy_number = request.form['policy_number']
        record.policy_type = request.form['policy_type']
        record.coverage_start = datetime.strptime(request.form['coverage_start'], '%Y-%m-%d').date()
        record.coverage_end = datetime.strptime(request.form['coverage_end'], '%Y-%m-%d').date()
        record.coverage_amount = float(request.form['coverage_amount'])
        record.copayment = float(request.form.get('copayment', 0))
        record.status = request.form['status']
        record.remarks = request.form.get('remarks', '')

        # Update patient_user_id if patient changed
        patient = Patient.query.filter_by(patient_id=request.form['patient_id']).first()
        if patient:
            record.patient_user_id = patient.user_id

        db.session.commit()
        flash('Insurance record updated successfully', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating insurance record: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_PATIENT)


@admin.route(INSURANCE_PATIENT_DELETE_RECORDS + '/<int:record_id>', methods=['POST'])
@token_required
def delete_record(current_user, record_id):
    try:
        record = InsuranceRecord.query.get_or_404(record_id)
        record.is_deleted = True
        record.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Insurance record deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting insurance record', 'danger')
    return redirect(ADMIN + INSURANCE_PATIENT)


@admin.route(INSURANCE_PATIENT_RESTORE_RECORDS + '/<int:record_id>', methods=['POST'],
             endpoint="insurance_record_restore")
@token_required
def restore_record(current_user, record_id):
    try:
        record = InsuranceRecord.query.get_or_404(record_id)
        record.is_deleted = False
        record.deleted_at = None
        db.session.commit()
        flash('Insurance record deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting insurance record', 'danger')
    return redirect(ADMIN + INSURANCE_PATIENT)
