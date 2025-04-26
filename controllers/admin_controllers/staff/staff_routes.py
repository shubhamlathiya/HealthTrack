from sqlite3 import IntegrityError

from flask import render_template, request, redirect, flash
from datetime import datetime

from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import STAFF, STAFF_ADD, ADMIN, STAFF_EDIT, STAFF_DELETE, STAFF_RESTORE
from models.departmentModel import Department
from models.staffModel import Staff
from models.userModel import User
from utils.config import db
from utils.email_utils import send_email


# All Staff
@admin.route(STAFF, methods=['GET'], endpoint='all-staff')
def all_staff():
    active_staff = Staff.query.filter_by(is_deleted=False).all()
    departments = Department.query.filter_by(is_deleted=False).all()
    deleted_staff = Staff.query.filter_by(is_deleted=True).all()
    return render_template('admin_templates/staff/staff.html',
                           staff_list=active_staff,
                           departments=departments,
                           deleted_staff=deleted_staff)


# Add Staff

@admin.route(STAFF_ADD, methods=['POST'], endpoint='add-staff')
def add_staff():
    try:
        # Check if email already exists
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email address already exists!', 'danger')
            return redirect(ADMIN + STAFF)

        # Handle file upload
        profile_pic = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join('static', 'uploads', 'staff')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                profile_pic = os.path.join('uploads', 'staff', filename)

        # Create user first
        user = User(
            email=request.form['email'],
            password=generate_password_hash(request.form['password']),
            role='staff',  # Default role for staff members
            status=True if request.form['status'] == 'Active' else False,
            verified=False  # Will be verified after email confirmation
        )
        db.session.add(user)
        db.session.flush()  # To get the user ID

        # Create staff profile
        staff = Staff(
            user_id=user.id,
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            mobile=request.form['mobile'],
            designation=request.form['designation'],
            department_id=request.form['department'],
            joining_date=datetime.strptime(request.form['joining_date'], '%Y-%m-%d').date(),
            salary=float(request.form['salary']),
            status=request.form['status'],
            shift=request.form['shift'],
            experience=int(request.form['experience']),
            gender=request.form['gender'],
            address=request.form['address'],
            date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date(),
            education=request.form['education'],
            profile_picture=profile_pic
        )

        db.session.add(staff)
        db.session.commit()

        verification_link = f"http://localhost:5000/auth/verify-email/{user.id}"
        send_email('Verify Your Email', user.email, verification_link)

        flash('Staff member added successfully! Verification email sent.', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data: {str(e)}', 'danger')
    except IntegrityError as e:
        db.session.rollback()
        flash('Database error occurred. Please try again.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding staff: {str(e)}', 'danger')

    return redirect(ADMIN + STAFF)


# Edit Staff
@admin.route(STAFF_EDIT + '/<int:id>', methods=['POST'], endpoint='edit-staff')
def edit_staff(id):
    staff = Staff.query.get_or_404(id)
    # user = staff.user

    try:
        # Update user account if email changed
        # if user.email != request.form['email']:
        #     if User.query.filter(User.email == request.form['email'], User.id != user.id).first():
        #         flash('Email address already in use!', 'danger')
        #         return redirect(ADMIN + STAFF)
        #     user.email = request.form['email']
        #
        # # Update password if provided
        # if request.form['password']:
        #     user.password = generate_password_hash(request.form['password'])
        #
        # user.status = True if request.form['status'] == 'Active' else False
        # user.updated_at = datetime.utcnow()

        # Handle file upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file.filename != '':
                # Delete old file if exists
                if staff.profile_picture:
                    old_file = os.path.join('static', staff.profile_picture)
                    if os.path.exists(old_file):
                        os.remove(old_file)

                # Save new file
                filename = secure_filename(file.filename)
                upload_folder = os.path.join('static', 'uploads', 'staff')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                staff.profile_picture = os.path.join('uploads', 'staff', filename)

        # Update staff details
        staff.first_name = request.form['first_name']
        staff.last_name = request.form['last_name']
        staff.mobile = request.form['mobile']
        staff.designation = request.form['designation']
        staff.department_id = request.form['department']
        staff.joining_date = datetime.strptime(request.form['joining_date'], '%Y-%m-%d').date()
        staff.salary = float(request.form['salary'])
        staff.work_status = request.form['status']
        staff.shift = request.form['shift']
        staff.experience = int(request.form['experience'])
        staff.gender = request.form['gender']
        staff.address = request.form['address']
        staff.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
        staff.education = request.form['education']

        db.session.commit()
        flash('Staff member updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating staff: {str(e)}', 'danger')

    return redirect(ADMIN + STAFF)


# Delete Staff (Soft Delete)
@admin.route(STAFF_DELETE + '/<int:id>', methods=['POST'], endpoint="delete-staff")
def delete_staff(id):
    staff = Staff.query.get_or_404(id)
    user = staff.user
    try:
        staff.is_deleted = True
        staff.deleted_at = datetime.now()

        # Also deactivate user account
        user.status = False
        user.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Staff member deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting staff: {str(e)}', 'danger')
    return redirect(ADMIN + STAFF)


# Restore Staff
@admin.route(STAFF_RESTORE + '/<int:id>', methods=['POST'], endpoint="restore-staff")
def restore_staff(id):
    staff = Staff.query.get_or_404(id)
    user = staff.user
    try:
        staff.is_deleted = False
        staff.deleted_at = None

        # Reactivate user account
        user.status = True
        user.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Staff member restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring staff: {str(e)}', 'danger')
    return redirect(ADMIN + STAFF)
