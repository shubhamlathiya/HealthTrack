from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DEPARTMENT_LIST, DEPARTMENT_ADD_DEPARTMENT


@admin.route(DEPARTMENT_LIST, methods=['GET'], endpoint='departments-list')
def department_list():
    return render_template("admin_templates/department/departments-list.html")

@admin.route(DEPARTMENT_ADD_DEPARTMENT, methods=['GET'], endpoint='add-department')
def department_list():
    return render_template("admin_templates/department/add-department.html")