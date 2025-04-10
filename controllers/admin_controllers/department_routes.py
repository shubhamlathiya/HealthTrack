from flask import render_template, request, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DEPARTMENT_LIST, DEPARTMENT_ADD_DEPARTMENT
from models.departmentModel import Department
from utils.config import db


@admin.route(DEPARTMENT_LIST, methods=['GET'], endpoint='departments-list')
def department_list():
    return render_template("admin_templates/department/departments-list.html")


@admin.route(DEPARTMENT_ADD_DEPARTMENT, methods=['GET'], endpoint='add-department')
def department_list():
    return render_template("admin_templates/department/add-department.html")


@admin.route(DEPARTMENT_ADD_DEPARTMENT, methods=['POST'])
def add_department():
    name = request.form.get('name')
    email = request.form.get('email')
    head = request.form.get('head')
    phone = request.form.get('phone')
    status = request.form.get('status') == 'active'
    message = request.form.get('message')

    # Create new department
    new_dept = Department(
        name=name,
        email=email,
        department_head=head,
        phone=phone,
        status=status,
        message=message
    )

    try:
        db.session.add(new_dept)
        db.session.commit()

        return redirect("/admin/" + DEPARTMENT_LIST)
    except Exception as e:
        db.session.rollback()
        print(f'Error adding department: {str(e)}', 'danger')
