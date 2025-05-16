from flask import render_template

from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models.userModel import UserRole


@patients.route('/dashboard' , methods=['GET'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def dashboard(current_user):
    return render_template("patient_templates/dashboard/dashboard.html")
