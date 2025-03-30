from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/dashboard', methods=['GET'] , endpoint='dashboard')
def dashboard():
    return render_template("admin_templates/admin_dashboard_templets.html")
