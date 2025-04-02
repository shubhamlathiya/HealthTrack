from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/insurance/patient', methods=['GET'], endpoint='insurance_patient')
def dashboard():
    return render_template("admin_templates/insurance/patient_insurance.html")


@admin.route('/insurance/provider', methods=['GET'], endpoint='insurance_provider')
def dashboard():
    return render_template("admin_templates/insurance/insurance_providers.html")