from flask import render_template, request, flash, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DOCTOR_ASSIGN_DEPARTMENT, ADMIN, DOCTOR_UPDATE_ASSIGN_DEPARTMENT
from middleware.auth_middleware import token_required
from models.departmentAssignmentModel import DepartmentAssignment
from models.departmentModel import Department
from models.doctorModel import Doctor
from models.userModel import UserRole
from utils.config import db


@admin.route(DOCTOR_ASSIGN_DEPARTMENT, methods=['GET'], endpoint="department_assignments")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def department_assignments(current_user):
    try:
        doctors = Doctor.query.options(
            db.joinedload(Doctor.department_assignments)
            .joinedload(DepartmentAssignment.department)
        ).filter(
            Doctor.is_deleted == False
        ).order_by(Doctor.last_name, Doctor.first_name).all()

        # Get all active departments
        departments = Department.query.filter(
            Department.is_deleted == False,
            Department.status == True
        ).order_by(Department.name).all()

        for doc in doctors:
            for da in doc.department_assignments:
                print(f"{doc.first_name} - {da.department.name if da.department else 'MISSING DEPARTMENT'}")

        return render_template('admin_templates/doctor/assign_department.html',
                               doctors=doctors,
                               departments=departments,
                               ADMIN=ADMIN,
                               DOCTOR_ASSIGN_DEPARTMENT = DOCTOR_ASSIGN_DEPARTMENT,
                               DOCTOR_UPDATE_ASSIGN_DEPARTMENT = DOCTOR_UPDATE_ASSIGN_DEPARTMENT)
    except Exception as e:
        return "An error occurred while loading the department assignment page.", 500


@admin.route(DOCTOR_ASSIGN_DEPARTMENT, methods=['POST'], endpoint="assign_doctor_department")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def assign_doctor_department(current_user):
    try:
        data = request.form
        doctor_id = data.get('doctor_id')
        department_id = data.get('department_id')

        # Check if this doctor already has an active assignment in this department
        existing_assignment = DepartmentAssignment.query.filter_by(
            doctor_id=doctor_id,
            department_id=department_id,
            current_status='active'
        ).first()

        if existing_assignment:
            flash('This doctor already has an active assignment in this department', 'warning')
            return redirect("/department-assignments1")

        # Create new assignment
        new_assignment = DepartmentAssignment(
            doctor_id=doctor_id,
            department_id=department_id,
            specialty=data.get('specialty'),
            experience_level=data.get('experience_level'),
            current_status=data.get('current_status', 'Pending'),
            notes=data.get('notes')
        )

        # Deactivate any other active assignments for this doctor
        DepartmentAssignment.query.filter_by(
            doctor_id=doctor_id,
            current_status='Active'
        ).update({'current_status': 'Inactive'})

        db.session.add(new_assignment)
        db.session.commit()

        flash('Department assignment created successfully!', 'success')
        return redirect(ADMIN + DOCTOR_ASSIGN_DEPARTMENT)

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating assignment: {str(e)}', 'danger')
        return redirect(ADMIN + DOCTOR_ASSIGN_DEPARTMENT)


@admin.route(DOCTOR_UPDATE_ASSIGN_DEPARTMENT + '/<int:assignment_id>', methods=['POST'] ,endpoint="update_assignment")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def update_assignment(current_user, assignment_id):
    try:
        assignment = DepartmentAssignment.query.get_or_404(assignment_id)
        data = request.form

        # Update assignment
        assignment.specialty = data.get('specialty')
        assignment.experience_level = data.get('experience_level')
        assignment.current_status = data.get('current_status')
        assignment.notes = data.get('notes')

        # If status changed to Active, deactivate other active assignments
        if assignment.current_status == 'Active':
            DepartmentAssignment.query.filter(
                DepartmentAssignment.doctor_id == assignment.doctor_id,
                DepartmentAssignment.id != assignment.id,
                DepartmentAssignment.current_status == 'Active'
            ).update({'current_status': 'Inactive'})

        db.session.commit()
        flash('Assignment updated successfully!', 'success')
        return redirect(ADMIN + DOCTOR_ASSIGN_DEPARTMENT)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating assignment: {str(e)}', 'danger')
        return redirect(ADMIN + DOCTOR_ASSIGN_DEPARTMENT)
