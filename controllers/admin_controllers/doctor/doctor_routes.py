from flask import render_template, request, jsonify, redirect
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DOCTOR_ADD_DOCTOR, DOCTOR_LIST
from models.doctorModel import Availability, Doctor
from models.userModel import User
from utils.config import db
from utils.email_utils import send_email

UPLOAD_FOLDER = 'uploads/profile_pictures'  # Base folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin.route(DOCTOR_LIST, methods=['GET'], endpoint='doctor_list')
def doctor_list():
    # Query all doctors ordered by most recent first
    doctors = Doctor.query.order_by(Doctor.created_at.desc()).all()

    # Preload department names for each doctor to avoid N+1 queries
    for doctor in doctors:
        doctor.department_names = [dept.department.name for dept in doctor.department_assignments]

    return render_template(
        "admin_templates/doctor/doctor_list.html",
        doctors=doctors
    )


@admin.route(DOCTOR_ADD_DOCTOR, methods=['GET'], endpoint='add_doctor')
def department_list():
    return render_template("admin_templates/doctor/add-doctors.html")


@admin.route(DOCTOR_ADD_DOCTOR, methods=['POST'])
def register_doctor():
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
            role='doctor',
            status=True,
            verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        # 2. Create Doctor without profile_picture for now
        new_doctor = Doctor(
            user_id=new_user.id,
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
                    day_of_week=day,
                    from_time=from_time,
                    to_time=to_time,
                    doctor_id=new_doctor.id
                )
                db.session.add(availability)

        db.session.commit()

        print(1)
        # Send a verification email (You should have your email setup)
        verification_link = f"http://localhost:5000/auth/verify-email/{new_user.id}"
        send_email('Verify Your Email', email, verification_link)
        print(2)
        # return jsonify({
        #     'success': True,
        #     'message': 'Doctor registered successfully',
        #     'doctor_id': new_doctor.id
        # }), 201

        return redirect("/admin/" + DOCTOR_ADD_DOCTOR)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
