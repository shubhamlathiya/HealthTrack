# from flask import render_template
#
# from controllers.admin_controllers import admin
#
#
from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DOCTOR_ADD_DOCTOR


@admin.route(DOCTOR_ADD_DOCTOR, methods=['GET'], endpoint='add_doctor')
def department_list():
    return render_template("admin_templates/doctor/add-doctors.html")