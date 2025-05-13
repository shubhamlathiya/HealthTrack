from datetime import datetime, date

from flask import render_template, request, jsonify, redirect
from sqlalchemy import func, and_

from controllers.doctor_controllers import doctors
from middleware.auth_middleware import token_required
from models import Department
from models.appointmentModel import Appointment
from models.doctorModel import Doctor
from utils.config import db


@doctors.route('/appointment', methods=['GET'], endpoint='calendar-events')
def appointment_calendar():
    """Render the appointment calendar view"""
    return render_template('doctor_templates/appointments/appointment_management.html')


@doctors.route('/view-appointment', methods=['GET'], endpoint='viewAppointment')
@token_required
def viewAppointment(current_user):
    doctors = Doctor.query.filter_by(user_id=current_user).first()
    if not doctors:
        return redirect(request.url)
    departments = Department.query.filter_by(is_deleted=False).all()
    appointments = Appointment.query.filter_by(doctor_id=doctors.id, is_deleted=False).all()
    deleted_appointments = Appointment.query.filter_by(doctor_id=doctors.id, is_deleted=True).all()
    return render_template('doctor_templates/appointments/appointment_list.html', appointments=appointments,
                           deleted_appointments=deleted_appointments,
                           departments=departments,
                           date=date
                           )

@doctors.route('/calendar-events')
@token_required
def get_calendar_events(current_user):
    """Get appointment counts for calendar view"""
    doctor = Doctor.query.filter_by(user_id=current_user).first()
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    doctor_id = doctor.id

    # Get counts of appointments per day
    appointment_counts = db.session.query(
        Appointment.date,
        func.count(Appointment.id).label('count')
    ).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.is_deleted == False,
            Appointment.status.in_(['scheduled', 'Completed', 'forwarded', 'canceled'])
        )
    ).group_by(Appointment.date).all()

    events = []
    for appt_date, count in appointment_counts:
        if count > 0:
            events.append({
                'title': f"{count} Appointment{'s' if count > 1 else ''}",
                'url': f"/doctor/appointments/list?date={appt_date.isoformat()}",
                'start': appt_date.isoformat(),
                'textColor': '#566fe2',
                'color': '#ffffff',
                'borderColor': '#566fe2'
            })

    return jsonify(events)


@doctors.route('/appointments/list')
@token_required
def appointment_list(current_user):
    """Show list of appointments for a specific date"""
    doctor = Doctor.query.filter_by(user_id=current_user).first()
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    doctor_id = doctor.id

    selected_date = request.args.get('date', date.today().isoformat())

    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()

    # Get all appointments for the selected date
    appointments = Appointment.query.filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.date == selected_date,
            Appointment.is_deleted == False
        )
    ).order_by(Appointment.start_time).all()

    departments = Department.query.filter_by(is_deleted=False).all()
    return render_template('doctor_templates/appointments/appointment_list.html',
                           appointments=appointments,
                           selected_date=selected_date,
                           departments=departments,
                           date=date)
