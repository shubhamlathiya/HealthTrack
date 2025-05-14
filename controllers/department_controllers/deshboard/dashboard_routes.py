from flask import render_template

from controllers.department_controllers import department
from middleware.auth_middleware import token_required
from models.doctorModel import Doctor
from models.userModel import User


@department.route('/dashboard', methods=['GET'], endpoint='department_dashboard')
@token_required
def department_dashboard(current_user):
    users = User.query.filter(User.id == current_user).first()
    print(users)

    doctors = Doctor.query.filter_by(user_id=users.id).first()
    print(doctors)
    return render_template("department_templates/dashboard/department_dashboard_templets.html",
                           users=users, doctors=doctors)
