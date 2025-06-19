from datetime import datetime, timedelta

from flask import render_template

from controllers.admin_controllers import admin
from middleware.auth_middleware import token_required
from models import Patient, Appointment
from models.doctorModel import Doctor
from models.userModel import UserRole


@admin.route('/dashboard', methods=['GET'], endpoint='admin_dashboard')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def admin_dashboard(current_user):
    today = datetime.now()
    start_of_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0,
                                                                            microsecond=0)

    total_patients = Patient.query.count()
    patients_this_month = Patient.query.filter(Patient.created_at >= start_of_this_month).count()

    total_appointments = Appointment.query.count()
    appointments_this_month = Appointment.query.filter(Appointment.date >= start_of_this_month).count()

    completed_appointments = Appointment.query.filter_by(status='Completed').count()
    revenue_per_appointment = 50  # Example: average revenue per appointment in dollars
    estimated_total_revenue = completed_appointments * revenue_per_appointment

    completed_appointments_this_month = Appointment.query.filter(
        Appointment.status == 'Completed',
        Appointment.date >= start_of_this_month
    ).count()
    estimated_revenue_this_month = completed_appointments_this_month * revenue_per_appointment

    available_doctors = Doctor.query.order_by(Doctor.created_at.desc()).limit(3).all()

    # Pass the collected data to the template
    return render_template(
        "admin_templates/dashboard/admin_dashboard_templets.html",
        total_patients=total_patients,
        patients_this_month=patients_this_month,
        total_appointments=total_appointments,
        appointments_this_month=appointments_this_month,
        estimated_total_revenue=estimated_total_revenue,
        estimated_revenue_this_month=estimated_revenue_this_month,
        available_doctors=available_doctors,
    )
