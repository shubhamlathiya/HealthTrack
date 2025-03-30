from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template("admin/admin_dashboard_templets.html")
