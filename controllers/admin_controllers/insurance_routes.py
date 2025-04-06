from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import INSURANCE_PATIENT, INSURANCE_PROVIDER, INSURANCE_CLAIM_STATUS


@admin.route(INSURANCE_PATIENT, methods=['GET'], endpoint='insurance_patient')
def insurance_patient():
    return render_template("admin_templates/insurance/patient_insurance.html")


@admin.route(INSURANCE_PROVIDER, methods=['GET'], endpoint='insurance_provider')
def insurance_provider():
    return render_template("admin_templates/insurance/insurance_providers.html")

@admin.route(INSURANCE_CLAIM_STATUS, methods=['GET'], endpoint='insurance_claim_status')
def insurance_claim_status():
    return render_template("admin_templates/insurance/claim_status.html")