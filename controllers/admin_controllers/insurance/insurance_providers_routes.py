from datetime import datetime

from flask import render_template, redirect, url_for, flash, request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import INSURANCE_PROVIDER, ADMIN, INSURANCE_EDIT_INSURANCE_PROVIDER, \
    INSURANCE_DELETE_INSURANCE_PROVIDER, INSURANCE_RESTORE_INSURANCE_PROVIDER, INSURANCE_ADD_INSURANCE_PROVIDER
from middleware.auth_middleware import token_required
from models.insuranceProviderModel import InsuranceProvider, CoverageType
from utils.config import db


# List all insurance providers
@admin.route(INSURANCE_PROVIDER, methods=['GET'], endpoint='admin_insurance_providers')
@token_required
def list_providers(current_user):
    try:
        # Get active providers (not deleted) with their coverage types
        providers = InsuranceProvider.query \
            .filter_by(is_deleted=False) \
            .options(db.joinedload(InsuranceProvider.coverages)) \
            .order_by(InsuranceProvider.name) \
            .all()

        # Get deleted providers
        deleted_providers = InsuranceProvider.query \
            .filter_by(is_deleted=True) \
            .order_by(InsuranceProvider.deleted_at.desc()) \
            .all()

        # Get all active coverage types for the form
        coverage_types = CoverageType.query \
            .filter_by(is_deleted=False) \
            .order_by(CoverageType.name) \
            .all()

        # Calculate statistics for the dashboard
        status_counts = db.session.query(
            InsuranceProvider.status,
            db.func.count(InsuranceProvider.id)
        ).filter_by(is_deleted=False) \
            .group_by(InsuranceProvider.status) \
            .all()

        stats = {
            'total': len(providers),
            'active': next((count for status, count in status_counts if status == 'Active'), 0),
            'inactive': next((count for status, count in status_counts if status == 'Inactive'), 0),
            'pending_renewal': next((count for status, count in status_counts if status == 'Renewal Pending'), 0)
        }

        return render_template(
            'admin_templates/insurance/insurance_providers.html',
            providers=providers,
            deleted_providers=deleted_providers,
            coverage_types=coverage_types,
            stats=stats,
            current_time=datetime.utcnow()
        )

    except Exception as e:
        flash(f'An error occurred while loading insurance providers: {str(e)}', 'danger')
        return render_template(
            'admin_templates/insurance/insurance_providers.html',
            providers=[],
            deleted_providers=[],
            coverage_types=[],
            stats={'total': 0, 'active': 0, 'inactive': 0, 'pending_renewal': 0},
            current_time=datetime.utcnow()
        )


@admin.route(INSURANCE_ADD_INSURANCE_PROVIDER, methods=['POST'], endpoint="add_provide")
@token_required
def add_provider(current_user):
    try:
        # Get form data
        name = request.form.get('name')
        code = request.form.get('code')
        website = request.form.get('website')
        phone = request.form.get('phone')
        email = request.form.get('email')
        support_phone = request.form.get('support_phone')
        address = request.form.get('address')
        contract_start = request.form.get('contract_start')
        contract_end = request.form.get('contract_end')
        reimbursement_rate = request.form.get('reimbursement_rate')
        payment_terms = request.form.get('payment_terms')
        notes = request.form.get('notes')
        status = request.form.get('status')
        selected_coverages = request.form.getlist('coverages')

        # Validate required fields
        required_fields = {
            'Name': name,
            'Code': code,
            'Phone': phone,
            'Email': email,
            'Contract Start': contract_start,
            'Contract End': contract_end,
            'Reimbursement Rate': reimbursement_rate,
            'Status': status
        }

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            flash(f'Missing required fields: {", ".join(missing_fields)}', 'danger')
            return redirect(url_for('admin.admin_insurance_providers'))

        # Check if provider code already exists
        if InsuranceProvider.query.filter(
                or_(
                    InsuranceProvider.code == code,
                    InsuranceProvider.name == name
                ),
                InsuranceProvider.is_deleted == False
        ).first():
            flash('Provider with this code or name already exists', 'danger')
            return redirect(url_for('admin.admin_insurance_providers'))

        # Create new provider
        new_provider = InsuranceProvider(
            name=name,
            code=code,
            website=website,
            phone=phone,
            email=email,
            support_phone=support_phone,
            address=address,
            contract_start=datetime.strptime(contract_start, '%Y-%m-%d').date(),
            contract_end=datetime.strptime(contract_end, '%Y-%m-%d').date(),
            reimbursement_rate=float(reimbursement_rate),
            payment_terms=payment_terms,
            notes=notes,
            status=status
        )

        # Add selected coverage types
        for coverage_id in selected_coverages:
            coverage = CoverageType.query.get(coverage_id)
            if coverage and not coverage.is_deleted:
                new_provider.coverages.append(coverage)

        db.session.add(new_provider)
        db.session.commit()
        flash('Insurance provider added successfully!', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except IntegrityError:
        db.session.rollback()
        flash('Database integrity error. Please check your data.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding provider: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_PROVIDER)


@admin.route(INSURANCE_EDIT_INSURANCE_PROVIDER + '/<int:provider_id>', methods=['POST'], endpoint="edit_provider")
@token_required
def edit_provider(current_user, provider_id):
    provider = InsuranceProvider.query.get_or_404(provider_id)

    try:
        # Get form data
        name = request.form.get('name')
        code = request.form.get('code')
        website = request.form.get('website')
        phone = request.form.get('phone')
        email = request.form.get('email')
        support_phone = request.form.get('support_phone')
        address = request.form.get('address')
        contract_start = request.form.get('contract_start')
        contract_end = request.form.get('contract_end')
        reimbursement_rate = request.form.get('reimbursement_rate')
        payment_terms = request.form.get('payment_terms')
        notes = request.form.get('notes')
        status = request.form.get('status')
        selected_coverages = request.form.getlist('coverages')

        # Validate required fields
        required_fields = {
            'Name': name,
            'Code': code,
            'Phone': phone,
            'Email': email,
            'Contract Start': contract_start,
            'Contract End': contract_end,
            'Reimbursement Rate': reimbursement_rate,
            'Status': status
        }

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            flash(f'Missing required fields: {", ".join(missing_fields)}', 'danger')
            return redirect(url_for('admin.admin_insurance_providers'))

        # Check if another provider has this code or name
        existing_provider = InsuranceProvider.query.filter(
            or_(
                InsuranceProvider.code == code,
                InsuranceProvider.name == name
            ),
            InsuranceProvider.id != provider_id,
            InsuranceProvider.is_deleted == False
        ).first()

        if existing_provider:
            flash('Another provider with this code or name already exists', 'danger')
            return redirect(url_for('admin.admin_insurance_providers'))

        # Update provider data
        provider.name = name
        provider.code = code
        provider.website = website
        provider.phone = phone
        provider.email = email
        provider.support_phone = support_phone
        provider.address = address
        provider.contract_start = datetime.strptime(contract_start, '%Y-%m-%d').date()
        provider.contract_end = datetime.strptime(contract_end, '%Y-%m-%d').date()
        provider.reimbursement_rate = float(reimbursement_rate)
        provider.payment_terms = payment_terms
        provider.notes = notes
        provider.status = status
        provider.updated_at = datetime.utcnow()

        # Update coverage types
        provider.coverages = []
        for coverage_id in selected_coverages:
            coverage = CoverageType.query.get(coverage_id)
            if coverage and not coverage.is_deleted:
                provider.coverages.append(coverage)

        db.session.commit()
        flash('Insurance provider updated successfully!', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except IntegrityError:
        db.session.rollback()
        flash('Database integrity error. Please check your data.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating provider: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_PROVIDER)


@admin.route(INSURANCE_DELETE_INSURANCE_PROVIDER + '/<int:provider_id>', methods=['POST'],
             endpoint="delete_insurance_provider")
@token_required
def delete_provider(current_user, provider_id):
    provider = InsuranceProvider.query.get_or_404(provider_id)

    try:
        # Soft delete the provider
        provider.is_deleted = True
        provider.deleted_at = datetime.utcnow()
        provider.status = 'Inactive'

        db.session.commit()
        flash('Insurance provider deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting provider: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_PROVIDER)


@admin.route(INSURANCE_RESTORE_INSURANCE_PROVIDER + '/<int:provider_id>', methods=['POST'],
             endpoint="restore_insurance_provider")
@token_required
def restore_provider(current_user, provider_id):
    provider = InsuranceProvider.query.get_or_404(provider_id)

    try:
        # Restore the provider
        provider.is_deleted = False
        provider.deleted_at = None

        # Check if contract is still valid
        current_date = datetime.utcnow().date()
        if provider.contract_end < current_date:
            provider.status = 'Renewal Pending'
        else:
            provider.status = 'Active'

        db.session.commit()
        flash('Insurance provider restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring provider: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_PROVIDER)
