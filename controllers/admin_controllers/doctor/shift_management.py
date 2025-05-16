from flask import request, render_template, jsonify

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DOCTOR_SHIFT_MANAGEMENT, DOCTOR_UPDATE_SHIFT_MANAGEMENT, ADMIN
from middleware.auth_middleware import token_required
from models.doctorModel import Doctor, Availability
from models.userModel import UserRole
from utils.config import db


@admin.route(DOCTOR_SHIFT_MANAGEMENT, methods=['GET'], endpoint='doctor-shifts')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def doctor_shifts(current_user):
    doctors = Doctor.query.options(db.joinedload(Doctor.availabilities)).all()

    days_map = {
        1: 'Monday', 2: 'Tuesday', 3: 'Wednesday',
        4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'
    }

    for doctor in doctors:
        schedule = {}
        for availability in doctor.availabilities:
            try:
                day_number = int(availability.day_of_week)  # Convert string to int if needed
            except ValueError:
                continue  # skip invalid values

            day_name = days_map.get(day_number)
            if day_name:
                schedule[day_name] = {
                    'start': availability.from_time,
                    'end': availability.to_time
                }

        doctor.temp_schedule = schedule  # Add it as a temp attribute

    return render_template('admin_templates/doctor/shift_management.html', doctors=doctors,
                           ADMIN = ADMIN,
                           DOCTOR_UPDATE_SHIFT_MANAGEMENT = DOCTOR_UPDATE_SHIFT_MANAGEMENT,
                           )


@admin.route(DOCTOR_UPDATE_SHIFT_MANAGEMENT + '/<int:doctor_id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def update_shifts(current_user, doctor_id):
    try:
        # Days map for lookup
        days_map = {
            'sunday': 1,
            'monday': 2,
            'tuesday': 3,
            'wednesday': 4,
            'thursday': 5,
            'friday': 6,
            'saturday': 7
        }

        for day_name, day_num in days_map.items():
            from_time = request.form.get(f'{day_name}_start')
            to_time = request.form.get(f'{day_name}_end')

            # Update existing availability or create new if exists
            availability = Availability.query.filter_by(doctor_id=doctor_id, day_of_week=day_num).first()

            if from_time == "None" or to_time == "None":
                if availability:
                    # Clear shift if marked "Not working"
                    availability.from_time = None
                    availability.to_time = None
            else:
                if availability:
                    availability.from_time = from_time
                    availability.to_time = to_time
                else:
                    new_shift = Availability(
                        doctor_id=doctor_id,
                        day_of_week=day_num,
                        from_time=from_time,
                        to_time=to_time
                    )
                    db.session.add(new_shift)

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
