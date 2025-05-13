import os

import uuid
from flask import flash, render_template, redirect, request, jsonify
from werkzeug.utils import secure_filename

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import INSURANCE_CLAIM_STATUS, GET_PATIENT, ADMIN, INSURANCE_NEW_CLAIM, \
    INSURANCE_CLAIM_STATUS_EDIT, INSURANCE_CLAIM_STATUS_PROCESS, INSURANCE_CLAIM_STATUS_APPEAL, \
    INSURANCE_CLAIM_STATUS_PRINT, INSURANCE_CLAIM_STATUS_DELETE, INSURANCE_CLAIM_STATUS_RESTORE
from middleware.auth_middleware import token_required
from models.insuranceProviderModel import InsuranceProvider, InsuranceClaim, InsuranceRecord
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

from datetime import datetime


@admin.route(INSURANCE_CLAIM_STATUS, methods=['GET'], endpoint='insurance_claims')
@token_required
def list_claims(current_user):
    try:
        # Base query with explicit joins using select_from
        claims = InsuranceClaim.query.filter(InsuranceClaim.is_deleted == False).all()

        # Calculate statistics
        stats = {
            'total': InsuranceClaim.query.filter_by(is_deleted=False).count(),
            'approved': InsuranceClaim.query.filter_by(status='Approved', is_deleted=False).count(),
            'pending': InsuranceClaim.query.filter_by(status='Pending', is_deleted=False).count(),
            'rejected': InsuranceClaim.query.filter_by(status='Rejected', is_deleted=False).count()
        }

        # Get deleted claims for restore modal
        deleted_claims = InsuranceClaim.query.filter_by(is_deleted=True).order_by(
            InsuranceClaim.deleted_at.desc()).all()

        insurance_records = db.session.query(InsuranceRecord). \
            join(InsuranceProvider, InsuranceRecord.insurance_provider_id == InsuranceProvider.id, isouter=True). \
            filter(InsuranceRecord.is_deleted == False). \
            filter(InsuranceProvider.status == 'Active'). \
            order_by(InsuranceRecord.coverage_end.desc()).all()

        return render_template(
            'admin_templates/insurance/claim_status.html',
            claims=claims,
            records=insurance_records,
            stats=stats,
            deleted_claims=deleted_claims,
            status_options=list(CLAIM_STATUS.values()),
            current_time=datetime.utcnow(),
            current_use=current_user
        )


    except Exception as e:
        db.session.rollback()  # Ensure that any failed transaction is rolled back
        flash(f'An error occurred while loading claims: {str(e)}', 'danger')
        return render_template(
            'admin_templates/insurance/claim_status.html',
            claims=[],
            patients=[],
            providers=[],
            stats={'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0},
            deleted_claims=[],
            status_options=[],
            current_user=current_user
        )


@admin.route(INSURANCE_NEW_CLAIM, methods=['POST'], endpoint='claims_add')
@token_required
def add_claim(current_user):
    try:
        print(request.form)
        # Handle file uploads
        claim_id = f"CLM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        docs = []

        for i, file in enumerate(request.files.getlist('documents')):
            if file.filename:
                ext = os.path.splitext(file.filename)[1]  # preserve original extension
                filename = f"{claim_id}_doc{i + 1}{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                docs.append(filename)

        # Get InsuranceRecord object
        insurance_record = InsuranceRecord.query.get(request.form['insurance_record_id'])
        if not insurance_record:
            flash('Invalid Insurance Record selected.', 'danger')
            return redirect(ADMIN + INSURANCE_CLAIM_STATUS)

        # Create claim
        claim = InsuranceClaim(
            claim_id=claim_id,
            patient_id=insurance_record.patient_id,
            patient_name=f"{insurance_record.patient_name}",
            service_date=datetime.strptime(request.form['service_date'], '%Y-%m-%d'),
            claim_date=datetime.utcnow().date(),
            diagnosis_code=request.form['diagnosis_code'],
            procedure_code=request.form['procedure_code'],
            claim_type=request.form['claim_type'],
            service_description=request.form['service_description'],
            claim_amount=float(request.form['claim_amount']),
            deductible=float(request.form.get('deductible', 0)),
            copayment=float(request.form.get('copayment', 0)),
            insurance_provider_id=insurance_record.insurance_provider_id,
            insurance_record_id=insurance_record.id,
            created_by=current_user,
            documents=",".join(docs),
            status=CLAIM_STATUS['PENDING'],
            remarks=request.form['notes']
        )

        db.session.add(claim)
        db.session.commit()
        flash('Claim submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting claim: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_CLAIM_STATUS)


@admin.route(INSURANCE_CLAIM_STATUS_EDIT + '/<int:claim_id>', methods=['POST'], endpoint='claims_edit')
@token_required
def edit_claim(current_user, claim_id):
    try:
        claim = InsuranceClaim.query.get_or_404(claim_id)

        # Handle file uploads if any new documents are added
        docs = claim.documents.split(',') if claim.documents else []

        for i, file in enumerate(request.files.getlist('documents')):
            if file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{claim.claim_id}_doc{len(docs) + i + 1}{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                docs.append(filename)

        # Update claim fields
        claim.service_date = datetime.strptime(request.form['service_date'], '%Y-%m-%d')
        claim.diagnosis_code = request.form['diagnosis_code']
        claim.procedure_code = request.form['procedure_code']
        claim.service_description = request.form['service_description']
        claim.claim_amount = float(request.form['claim_amount'])
        claim.claim_type = request.form['claim_type']
        claim.deductible = float(request.form.get('deductible', 0))
        claim.copayment = float(request.form.get('copayment', 0))
        claim.remarks = request.form.get('notes', '')
        claim.updated_by = current_user
        claim.updated_at = datetime.utcnow()

        if docs:  # Only update documents if new ones were added
            claim.documents = ",".join(docs)

        db.session.commit()
        flash('Claim updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating claim: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_CLAIM_STATUS)


@admin.route(INSURANCE_CLAIM_STATUS_PROCESS + '/<int:claim_id>', methods=['POST'], endpoint='insurance_claims_process')
@token_required
def process_insurance_claim(current_user, claim_id):
    try:
        claim = InsuranceClaim.query.get_or_404(claim_id)

        if claim.status not in [CLAIM_STATUS['PENDING'], CLAIM_STATUS['APPEAL']]:
            flash('Only pending or appeal claims can be processed', 'warning')
            return redirect(ADMIN + INSURANCE_CLAIM_STATUS)

        action = request.form.get('action')

        if action == 'approve':
            # Handle approval
            claim.status = CLAIM_STATUS['APPROVED']
            claim.approved_amount = float(request.form.get('approved_amount', claim.claim_amount))
            claim.processed_date = datetime.utcnow()
            flash('Claim approved successfully', 'success')

        elif action == 'reject':
            # Handle rejection
            claim.status = CLAIM_STATUS['REJECTED']
            claim.remarks = request.form.get('rejection_reason', 'No reason provided')
            claim.processed_date = datetime.utcnow()
            flash('Claim rejected', 'info')
        else:
            flash('Invalid action specified', 'danger')
            return redirect(ADMIN + INSURANCE_CLAIM_STATUS)

        db.session.commit()

    except ValueError as e:
        db.session.rollback()
        flash('Invalid numeric value provided', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing claim: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_CLAIM_STATUS)


@admin.route(INSURANCE_CLAIM_STATUS_APPEAL + '/<int:claim_id>', methods=['POST'], endpoint='insurance_claims_appeal')
@token_required
def appeal_insurance_claim(current_user, claim_id):
    try:
        claim = InsuranceClaim.query.get_or_404(claim_id)

        if claim.status != CLAIM_STATUS['REJECTED']:
            flash('Only rejected claims can be appealed', 'warning')
            return redirect(ADMIN + INSURANCE_CLAIM_STATUS)

        # Update claim with appeal information
        claim.appeal_reason = request.form['appeal_reason']
        claim.appeal_date = datetime.utcnow().date()
        claim.status = CLAIM_STATUS['APPEAL']
        claim.processed_by = None  # Reset for reprocessing
        claim.processed_date = None

        # Handle appeal documents
        if 'documentation' in request.files:
            document = request.files['documentation']
            if document.filename != '':
                filename = secure_filename(f"appeal_{claim.claim_id}_{document.filename}")
                filepath = os.path.join(APPEAL_FOLDER, filename)
                document.save(filepath)
                claim.appeal_documents = filename

        db.session.commit()
        flash('Claim appeal submitted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting appeal: {str(e)}', 'danger')
    return redirect(ADMIN + INSURANCE_CLAIM_STATUS)


@admin.route(INSURANCE_CLAIM_STATUS_PRINT + '/<int:claim_id>', methods=['GET'], endpoint='insurance_claims_print')
def print_insurance_claim(claim_id):
    try:
        claim = InsuranceClaim.query.get_or_404(claim_id)
        return render_template('admin_templates/insurance/print_claim.html', claim=claim)
    except Exception as e:
        flash('Error generating claim document', 'danger')
        return redirect(ADMIN + INSURANCE_CLAIM_STATUS)


@admin.route(INSURANCE_CLAIM_STATUS_DELETE + '/<int:claim_id>', methods=['POST'], endpoint='insurance_claims_delete')
@token_required
def delete_insurance_claim(current_user, claim_id):
    try:
        claim = InsuranceClaim.query.get_or_404(claim_id)

        if claim.status == CLAIM_STATUS['APPROVED']:
            flash('Approved claims cannot be deleted', 'warning')
            return redirect(ADMIN + INSURANCE_CLAIM_STATUS)

        claim.is_deleted = True
        claim.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Insurance claim deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting insurance claim', 'danger')
    return redirect(ADMIN + INSURANCE_CLAIM_STATUS)


@admin.route(INSURANCE_CLAIM_STATUS_RESTORE + '/<int:claim_id>', methods=['POST'], endpoint='insurance_claims_restore')
@token_required
def delete_insurance_claim(current_user, claim_id):
    try:
        claim = InsuranceClaim.query.get_or_404(claim_id)

        if claim.status == CLAIM_STATUS['APPROVED']:
            flash('Approved claims cannot be deleted', 'warning')
            return redirect(ADMIN + INSURANCE_CLAIM_STATUS)

        claim.is_deleted = False
        claim.deleted_at = None
        db.session.commit()
        flash('Insurance claim deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting insurance claim', 'danger')
    return redirect(ADMIN + INSURANCE_CLAIM_STATUS)