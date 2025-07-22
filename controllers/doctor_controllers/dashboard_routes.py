from datetime import datetime, timedelta

from flask import render_template, redirect, flash, session

from controllers.doctor_controllers import doctors
from middleware.auth_middleware import token_required
from models.appointmentModel import Appointment
from models.doctorModel import Doctor
from models.treatmentModel import Treatment
from models.userModel import UserRole


@doctors.route('/dashboard' , methods=['GET'] , endpoint='dashboard')
@token_required(allowed_roles=[UserRole.DOCTOR.name])
def dashboard(current_user):
    # Ensure user is logged in
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to access the dashboard.", "warning")
        return redirect("/")

    # Verify the user is a doctor
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    if not doctor:
        flash("Unauthorized access. Doctor profile not found.", "danger")
        return redirect("/")

    # Get today's date
    today = datetime.today().date()

    # Get doctor's upcoming appointments (today and future)
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= today
    ).order_by(Appointment.date, Appointment.start_time).all()

    # Group appointments by day
    appointments_by_day = {}
    for appt in appointments:
        day = appt.date.strftime('%A')  # Full day name (e.g., Monday)
        appointments_by_day.setdefault(day, []).append(appt)

    # Get recent appointments for approval (last 5 pending)
    recent_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'pending'
    ).order_by(Appointment.created_at.desc()).limit(5).all()

    # Get available treatments
    current_assignment = next(
        (assignment for assignment in doctor.department_assignments if assignment.current_status == 'Active'),
        None
    )

    # Now safely access the department_id and filter treatments
    if current_assignment:
        treatments = Treatment.query.filter_by(department_id=current_assignment.department_id).all()
    else:
        treatments = []  # or handle gracefully

    # Calculate earnings data (example - replace with your actual logic)
    earnings = {
        'online_consultation': 4900,
        'online_consultation_percent': 20,
        'overall_purchases': 750,
        'overall_purchases_percent': -26,  # Negative for decrease
        'pending_invoices': 560,
        'pending_invoices_percent': 28,
        'monthly_billing': 390,
        'monthly_billing_percent': 30
    }

    # Activity feed (example - replace with your actual activity log)
    activities = [
        {
            'doctor': f"Dr. {doctor.first_name} {doctor.last_name}",
            'action': "uploaded a prescription",
            'patient': "Ann Jordan",
            'timestamp': datetime.now() - timedelta(minutes=30)
        },
        {
            'doctor': f"Dr. {doctor.first_name} {doctor.last_name}",
            'action': "completed a patient examination",
            'patient': "Jody Ashley",
            'timestamp': datetime.now() - timedelta(hours=1)
        }
    ]

    # Chart data (example - replace with your actual data)
    patients_data = [10, 15, 12, 18, 20, 25, 22]
    appointments_data = [5, 8, 6, 9, 12, 15, 18]
    income_data = [2000, 3000, 2500, 4000, 3500, 5000, 4500]
    claims_data = [45, 25, 30]  # For donut chart

    # Growth percentages
    patient_growth = 20
    appointment_growth = 33
    income_increase = 22
    insurance_base_cover = 10000

    return render_template('doctor_templates/dashboard/doctor_dashboard_templets.html',
                           appointments_by_day=appointments_by_day,
                           appointments=appointments,
                           recent_appointments=recent_appointments,
                           treatments=treatments,
                           earnings=earnings,
                           activities=activities,
                           patients_data=patients_data,
                           appointments_data=appointments_data,
                           income_data=income_data,
                           claims_data=claims_data,
                           patient_growth=patient_growth,
                           appointment_growth=appointment_growth,
                           income_increase=income_increase,
                           insurance_base_cover=insurance_base_cover,
                           doctor=doctor
                           )
