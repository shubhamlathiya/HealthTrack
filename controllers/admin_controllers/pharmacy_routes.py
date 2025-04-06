from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import PHARMACY_MEDICINE_LIST


@admin.route(PHARMACY_MEDICINE_LIST, methods=['GET'], endpoint='medicine-list')
def pharmacy_medicine_list():
    return render_template("admin_templates/pharmacy/medicine_list.html")