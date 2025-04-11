from flask import render_template, request, flash, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DOCTOR_ASSIGN_DEPARTMENT
from models.departmentAssignmentModel import DepartmentAssignment
from models.departmentModel import Department
from models.doctorModel import Doctor
from utils.config import db


@admin.route(DOCTOR_ASSIGN_DEPARTMENT, methods=['GET'],endpoint="department_assignments")
def department_assignments():
    doctors = Doctor.query.options(
        db.joinedload(Doctor.assignments).joinedload(DepartmentAssignment.department)
    ).order_by(Doctor.last_name).all()

    departments = Department.query.order_by(Department.name).all()


    return render_template('admin_templates/doctor/assign_department.html',
                           doctors=doctors,
                           departments=departments)

@admin.route('/assign-doctor-department', methods=['POST'],endpoint="assign_doctor_department")
def assign_doctor_department():
    try:
        data = request.form
        doctor_id = data.get('doctor_id')
        department_id = data.get('department_id')

        # Check if this doctor already has an active assignment in this department
        existing_assignment = DepartmentAssignment.query.filter_by(
            doctor_id=doctor_id,
            department_id=department_id,
            current_status='Active'
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
        return redirect("/admin/" + DOCTOR_ASSIGN_DEPARTMENT)

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating assignment: {str(e)}', 'danger')
        return redirect("/admin/" + DOCTOR_ASSIGN_DEPARTMENT)

#
@admin.route('/update-assignment/<int:assignment_id>', methods=['POST'])
def update_assignment(assignment_id):
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
        return redirect("/admin/" + DOCTOR_ASSIGN_DEPARTMENT)

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating assignment: {str(e)}', 'danger')
        return redirect("/admin/" + DOCTOR_ASSIGN_DEPARTMENT)

