from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import (
    DEPARTMENT_MANAGE_HEADS
)
from middleware.auth_middleware import token_required
from models.departmentAssignmentModel import DepartmentAssignment


@admin.route(DEPARTMENT_MANAGE_HEADS + '/<int:department_id>', methods=['GET'], endpoint='manage-department-heads')
@token_required
def manage_department_heads(current_user, department_id):
    department = Department.query.get_or_404(department_id)
    current_heads = DepartmentHead.query.filter_by(
        department_id=department_id,
        is_active=True
    ).all()
    past_heads = DepartmentHead.query.filter_by(
        department_id=department_id,
        is_active=False
    ).order_by(DepartmentHead.end_date.desc()).all()


    available_doctors = Doctor.query.filter(
        ~Doctor.id.in_([head.doctor_id for head in current_heads]),
        Doctor.is_deleted == False
    ).all()

    return render_template("admin_templates/department/manage_department_heads.html",
                           department=department,
                           current_heads=current_heads,
                           past_heads=past_heads,
                           available_doctors=available_doctors,
                           ADMIN=ADMIN,
                           DEPARTMENT_LIST=DEPARTMENT_LIST,
                           DEPARTMENT_ADD_HEAD=DEPARTMENT_ADD_HEAD,
                           DEPARTMENT_REMOVE_HEAD=DEPARTMENT_REMOVE_HEAD
                           )


from datetime import datetime
from flask import render_template, request, redirect, flash
from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import (
    DEPARTMENT_LIST, DEPARTMENT_MANAGE_HEADS, DEPARTMENT_ADD_HEAD,
    DEPARTMENT_REMOVE_HEAD, ADMIN
)
from middleware.auth_middleware import token_required
from models.departmentModel import Department, DepartmentHead
from models.doctorModel import Doctor
from models.userModel import UserRole
from utils.config import db


@admin.route(DEPARTMENT_MANAGE_HEADS + '/<int:department_id>', methods=['GET'])
@token_required
def manage_department_heads(current_user, department_id):
    department = Department.query.get_or_404(department_id)

    current_heads = DepartmentHead.query.filter_by(
        department_id=department_id,
        is_active=True
    ).all()

    past_heads = DepartmentHead.query.filter_by(
        department_id=department_id,
        is_active=False
    ).order_by(DepartmentHead.end_date.desc()).all()

    # Get available doctors (not currently heads of any department)
    current_head_ids = [head.doctor_id for head in current_heads]
    available_doctors = Doctor.query.filter(
        ~Doctor.id.in_(current_head_ids),
        Doctor.is_deleted == False
    ).all()

    return render_template("admin_templates/department/manage_department_heads.html",
                           department=department,
                           current_heads=current_heads,
                           past_heads=past_heads,
                           available_doctors=available_doctors,
                           ADMIN=ADMIN,
                           DEPARTMENT_LIST=DEPARTMENT_LIST,
                           DEPARTMENT_ADD_HEAD=DEPARTMENT_ADD_HEAD,
                           DEPARTMENT_REMOVE_HEAD=DEPARTMENT_REMOVE_HEAD)


@admin.route(DEPARTMENT_ADD_HEAD + '/<int:department_id>', methods=['POST'])
@token_required
def add_department_head(current_user, department_id):
    try:
        # Get form data
        doctor_id = request.form.get('doctor_id')
        specialty = request.form.get('specialty')
        experience_level = request.form.get('experience_level')
        current_status = request.form.get('current_status', 'Active')
        start_date = request.form.get('start_date')
        notes = request.form.get('notes')

        if not doctor_id:
            flash('Please select a doctor', 'danger')
            return redirect(ADMIN + DEPARTMENT_MANAGE_HEADS + f'/{department_id}')

        # Verify department exists
        department = Department.query.get_or_404(department_id)

        # Verify doctor exists
        doctor = Doctor.query.get_or_404(doctor_id)
        if not doctor.user:
            flash('Selected doctor has no user account', 'danger')
            return redirect(ADMIN + DEPARTMENT_MANAGE_HEADS + f'/{department_id}')

        # Check if doctor is already head of any department
        existing_active_head = DepartmentHead.query.filter_by(
            doctor_id=doctor_id,
            is_active=True
        ).first()

        if existing_active_head:
            flash('This doctor is already head of another department', 'warning')
            return redirect(ADMIN + DEPARTMENT_MANAGE_HEADS + f'/{department_id}')

        # Deactivate any current head of this department
        current_head = DepartmentHead.query.filter_by(
            department_id=department_id,
            is_active=True
        ).first()

        if current_head:
            current_head.is_active = False
            current_head.end_date = datetime.utcnow()

            # Revert previous head's role
            prev_doctor = Doctor.query.get(current_head.doctor_id)
            if prev_doctor and prev_doctor.user:
                prev_doctor.user.role = UserRole.DOCTOR
                db.session.add(prev_doctor.user)

        # Create new department head
        new_head = DepartmentHead(
            department_id=department_id,
            doctor_id=doctor_id,
            start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.utcnow(),
            is_active=True
        )

        # Update new head's role
        doctor.user.role = UserRole.DEPARTMENT_HEAD
        db.session.add(doctor.user)
        db.session.add(new_head)

        # Create department assignment
        new_assignment = DepartmentAssignment(
            doctor_id=doctor_id,
            department_id=department_id,
            specialty=specialty,
            experience_level=experience_level,
            current_status=current_status,
            assigned_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.utcnow(),
            notes=notes
        )

        # Deactivate any other active assignments for this doctor in this department
        DepartmentAssignment.query.filter_by(
            doctor_id=doctor_id,
            department_id=department_id,
            current_status='Active'
        ).update({'current_status': 'Inactive'})

        db.session.add(new_assignment)
        db.session.commit()

        flash(f'Successfully assigned {doctor.first_name} {doctor.last_name} as department head', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning department head: {str(e)}', 'danger')

    return redirect(ADMIN + DEPARTMENT_MANAGE_HEADS + f'/{department_id}')


@admin.route(DEPARTMENT_REMOVE_HEAD + '/<int:head_id>', methods=['POST'])
@token_required
def remove_department_head(current_user, head_id):
    try:
        department_head = DepartmentHead.query.get_or_404(head_id)
        department_id = department_head.department_id
        doctor = Doctor.query.get_or_404(department_head.doctor_id)

        # Update department head record
        department_head.is_active = False
        department_head.end_date = datetime.utcnow()
        department_head.updated_at = datetime.utcnow()

        # Revert user role if user exists
        if doctor.user:
            doctor.user.role = UserRole.DOCTOR
            db.session.add(doctor.user)

        # Update any active assignments
        DepartmentAssignment.query.filter_by(
            doctor_id=doctor.id,
            department_id=department_id,
            current_status='Active'
        ).update({'current_status': 'Inactive'})

        db.session.commit()
        flash('Department head removed and role reverted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing department head: {str(e)}', 'danger')

    return redirect(ADMIN + DEPARTMENT_MANAGE_HEADS + f'/{department_id}')