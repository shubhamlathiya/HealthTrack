from datetime import datetime

from flask import render_template, request, flash, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import INSURANCE_PATIENT, INSURANCE_PROVIDER, INSURANCE_CLAIM_STATUS, \
    INSURANCE_ADD_INSURANCE_PROVIDER
from models.insuranceProviderModel import CoverageType, InsuranceProvider
from utils.config import db


@admin.route(INSURANCE_PATIENT, methods=['GET'], endpoint='insurance_patient')
def insurance_patient():
    return render_template("admin_templates/insurance/patient_insurance.html")


@admin.route(INSURANCE_ADD_INSURANCE_PROVIDER, methods=['GET'], endpoint='insurance_add_provider')
def insurance_add_insurance_provider():
    coverage_types = CoverageType.query.all()
    return render_template("admin_templates/insurance/add_insurance_providers.html", coverage_types=coverage_types)


@admin.route(INSURANCE_ADD_INSURANCE_PROVIDER, methods=['POST'])
def add_provider():
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
    required_fields = [name, code, phone, email, contract_start, contract_end, reimbursement_rate]
    if not all(required_fields):
        flash('Please fill all required fields', 'danger')
        return redirect("/admin/" + INSURANCE_ADD_INSURANCE_PROVIDER)

    # Check if provider code already exists
    if InsuranceProvider.query.filter_by(code=code).first():
        flash('Provider with this code already exists', 'danger')
        return redirect("/admin/" + INSURANCE_ADD_INSURANCE_PROVIDER)

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
        if coverage:
            new_provider.coverages.append(coverage)

    try:
        db.session.add(new_provider)
        db.session.commit()
        flash('Insurance provider added successfully!', 'success')
        return redirect("/admin/" + INSURANCE_ADD_INSURANCE_PROVIDER)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding provider: {str(e)}', 'danger')



@admin.route(INSURANCE_PROVIDER, methods=['GET'], endpoint='insurance_provider')
def insurance_provider():
    return render_template("admin_templates/insurance/insurance_providers.html")


@admin.route(INSURANCE_CLAIM_STATUS, methods=['GET'], endpoint='insurance_claim_status')
def insurance_claim_status():
    return render_template("admin_templates/insurance/claim_status.html")
