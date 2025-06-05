import os
import random
from datetime import datetime

from flask import render_template, request, jsonify, redirect, flash, session
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from controllers.constant.adminPathConstant import DOCTOR_ADD_DOCTOR, DOCTOR_LIST, ADMIN
from controllers.department_controllers import department
from middleware.auth_middleware import token_required
from models.departmentAssignmentModel import DepartmentAssignment
from models.doctorModel import Availability, Doctor
from models.userModel import User, UserRole
from utils.config import db
from utils.email_utils import send_email

UPLOAD_FOLDER = 'static/uploads/profile_pictures'  # Base folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@department.route(DOCTOR_LIST, methods=['GET'], endpoint='doctor_list')
@token_required(allowed_roles=[UserRole.DEPARTMENT_HEAD.name])
def doctor_list(current_user):
    # Get department_id from session
    department_id = session.get('department_id')

    if not department_id:
        flash("Department information not found", "error")
        return redirect("/admin/dashboard")  # Or appropriate fallback route

    # Query all doctors who are in the specified department and are active
    doctors = Doctor.query.join(DepartmentAssignment).filter(
        DepartmentAssignment.department_id == department_id,
        DepartmentAssignment.current_status == 'Active'
    ).order_by(Doctor.created_at.desc()).all()

    for doctor in doctors:
        doctor.department_names = [
            assignment.department.name
            for assignment in doctor.department_assignments
            if assignment.current_status == 'Active'
        ]
        # Add is_head flag to each doctor
        doctor.is_head = any(
            assignment.is_head and assignment.current_status == 'Active'
            for assignment in doctor.department_assignments
        )

    return render_template(
        "admin_templates/doctor/doctor_list.html",
        doctors=doctors,
        ADMIN=ADMIN,
        DOCTOR_ADD_DOCTOR=DOCTOR_ADD_DOCTOR,
    )


@department.route(DOCTOR_ADD_DOCTOR, methods=['GET'], endpoint='add_doctor')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def department_list(current_user):
    return render_template("admin_templates/doctor/add-doctors.html",
                           ADMIN=ADMIN,
                           DOCTOR_ADD_DOCTOR=DOCTOR_ADD_DOCTOR,
                           )


@department.route(DOCTOR_ADD_DOCTOR, methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def register_doctor(current_user):
    try:
        data = request.form
        print(data)
        # 1. Create User
        email = data.get('a5')
        password = data.get('u2')
        hashed_password = generate_password_hash(password)

        new_user = User(
            email=email,
            password=hashed_password,
            role=UserRole.DOCTOR,
            status=True,
            verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        current_date = datetime.utcnow()
        year = current_date.year
        month = f"{current_date.month:02d}"
        day = f"{current_date.day:02d}"

        # Generate random 2-digit number for uniqueness
        random_digits = random.randint(10, 99)

        # Create a unique user ID in the format of YYYYMMDDXX
        new_doctor_id = f"{year}{month}{day}{random_digits}"

        # 2. Create Doctor without profile_picture for now
        new_doctor = Doctor(
            user_id=new_user.id,
            doctor_id=new_doctor_id,
            first_name=data.get('a1'),
            last_name=data.get('a2'),
            age=data.get('a3'),
            gender=data.get('selectGenderOptions'),
            phone=data.get('a6'),
            qualification=data.get('a8'),
            designation=data.get('a9'),
            blood_group=data.get('a10'),
            address=data.get('a11'),
            bio=data.get('bio', ''),
            profile_picture=None  # Temp placeholder
        )
        db.session.add(new_doctor)
        db.session.commit()

        # 3. Now that we have the doctor ID, handle profile picture upload
        profile_pic = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)

                # Save the file
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                web_path = file_path.replace('\\', '/')
                file.save(web_path)
                profile_pic = web_path

                # Update doctor's profile_picture path
                new_doctor.profile_picture = profile_pic
                db.session.commit()

        # 4. Add availability records
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for i, day in enumerate(days, start=1):
            from_time = data.get(f'd{i}')  # e.g., "07:00 AM"
            to_time = data.get(f'd{i}X')  # e.g., "03:00 PM"

            # Skip if "Not working" (i.e., "None" or missing value)
            if from_time and to_time and from_time != 'None' and to_time != 'None':
                availability = Availability(
                    day_of_week=i,
                    from_time=from_time,
                    to_time=to_time,
                    doctor_id=new_doctor.id
                )
                db.session.add(availability)

        db.session.commit()

        body_html = render_template("email_templates/templates/welcome.html",
                                    user_name=new_doctor.first_name,
                                    new_user=new_doctor,
                                    temp_password=password,
                                    login_url="http://localhost:5000/")

        send_email('Welcome to HealthTrack Hospital', new_user.email, body_html)

        verification_token = new_user.generate_verification_token()
        verification_link = f"http://localhost:5000/auth/verify-email/{verification_token}"
        body_html = render_template("email_templates/templates/verification_mail.html",
                                    verification_link=verification_link,
                                    user_name=new_doctor.first_name)

        send_email('Verify Your Email', new_user.email, body_html)

        flash("Doctor registered successfully")
        return redirect("/admin/" + DOCTOR_ADD_DOCTOR)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
