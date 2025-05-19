from datetime import datetime

from flask import render_template, request, redirect, flash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DEPARTMENT_LIST, DEPARTMENT_ADD_DEPARTMENT, ADMIN, \
    DEPARTMENT_EDIT_DEPARTMENT, DEPARTMENT_DELETE_DEPARTMENT, DEPARTMENT_RESTORE_DEPARTMENT, DEPARTMENT_MANAGE_HEADS
from middleware.auth_middleware import token_required
from models.departmentModel import Department
from models.userModel import UserRole
from utils.config import db


@admin.route(DEPARTMENT_LIST, methods=['GET'], endpoint='departments-list')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def department_list(current_user):
    departments = Department.query.filter_by(is_deleted=0).order_by(Department.name.desc()).all()
    deleted_departments = Department.query.filter_by(is_deleted=1).order_by(Department.name.desc()).all()

    # Get associated doctors and rooms
    all_doctors = []
    for department in departments:
        for assignment in department.assignments:
            if str(assignment.current_status) == 'Active':
                print(assignment.current_status)
                all_doctors.append(assignment.doctor)

    all_rooms = [room for dept in departments for room in dept.rooms]

    return render_template("admin_templates/department/departments-list.html",
                           departments=departments,
                           deleted_departments=deleted_departments,
                           doctors=all_doctors,
                           rooms=all_rooms,
                           ADMIN=ADMIN,
                           DEPARTMENT_ADD_DEPARTMENT=DEPARTMENT_ADD_DEPARTMENT,
                           DEPARTMENT_EDIT_DEPARTMENT=DEPARTMENT_EDIT_DEPARTMENT,
                           DEPARTMENT_DELETE_DEPARTMENT=DEPARTMENT_DELETE_DEPARTMENT,
                           DEPARTMENT_RESTORE_DEPARTMENT=DEPARTMENT_RESTORE_DEPARTMENT,
                           DEPARTMENT_MANAGE_HEADS=DEPARTMENT_MANAGE_HEADS
                           )


@admin.route(DEPARTMENT_ADD_DEPARTMENT, methods=['GET'], endpoint='add-department')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def department_list(current_user):
    return render_template("admin_templates/department/add-department.html",
                           ADMIN=ADMIN,
                           DEPARTMENT_ADD_DEPARTMENT=DEPARTMENT_ADD_DEPARTMENT)


@admin.route(DEPARTMENT_ADD_DEPARTMENT, methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_department(current_user):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    status = request.form.get('status')
    message = request.form.get('message')

    # Create new department
    new_dept = Department(
        name=name,
        email=email,
        phone=phone,
        status=status,
        message=message
    )

    try:
        db.session.add(new_dept)
        db.session.commit()
        flash('Department added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding department: {str(e)}', 'danger')
    return redirect(ADMIN + DEPARTMENT_LIST)


@admin.route(DEPARTMENT_EDIT_DEPARTMENT + '/<int:id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_department(current_user, id):
    try:
        department = Department.query.get_or_404(id)

        # Update department data
        department.name = request.form.get('name')
        department.email = request.form.get('email')
        department.phone = request.form.get('phone')
        department.status = request.form.get('status')
        department.message = request.form.get('message')
        department.is_available = True if request.form.get('is_available') == '1' else False
        department.updated_at = datetime.utcnow()

        db.session.commit()

        flash('Department updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating department: {str(e)}', 'danger')
    return redirect(ADMIN + DEPARTMENT_LIST)


@admin.route(DEPARTMENT_DELETE_DEPARTMENT + '/<int:id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_department(current_user, id):
    try:
        department = Department.query.get_or_404(id)
        department.is_deleted = True
        # Soft delete (set deleted_at timestamp)
        department.deleted_at = datetime.utcnow()
        db.session.commit()

        flash('Department deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting department: {str(e)}', 'danger')
    return redirect(ADMIN + DEPARTMENT_LIST)


@admin.route(DEPARTMENT_RESTORE_DEPARTMENT + '/<int:id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_department(current_user, id):
    try:
        Department.query.filter_by(id=id).update({
            'is_deleted': False,
            'deleted_at': None
        })
        db.session.commit()

        flash('Department restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring department: {str(e)}', 'danger')
    return redirect(ADMIN + DEPARTMENT_LIST)
