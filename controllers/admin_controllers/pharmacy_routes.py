from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/pharmacy/medicine-list', methods=['GET'], endpoint='medicine-list')
def dashboard():
    return render_template("admin_templates/pharmacy/medicine_list.html")