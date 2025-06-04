from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.staffPathConstant import STAFF_DASHBOARD
from controllers.staff_controllers import staff
from middleware.auth_middleware import token_required
from models.userModel import UserRole


@staff.route(STAFF_DASHBOARD, methods=['GET'], endpoint='staff_dashboard')
@token_required(allowed_roles=[UserRole.STAFF.name])
def staff_dashboard(current_user):
    return render_template("staff_templates/dashboard/staff_dashboard_templets.html")
