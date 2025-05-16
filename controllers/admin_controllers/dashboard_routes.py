from flask import render_template

from controllers.admin_controllers import admin
from middleware.auth_middleware import token_required
from models.userModel import UserRole


@admin.route('/dashboard', methods=['GET'], endpoint='admin_dashboard')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def admin_dashboard(current_user):
    return render_template("admin_templates/dashboard/admin_dashboard_templets.html")
