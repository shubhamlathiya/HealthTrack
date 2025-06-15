from datetime import datetime, timedelta

from models import Appointment
from models.doctorModel import Availability


def generate_time_slots(start_time, end_time, existing_appointments, duration=30):
    """
    Generate available time slots considering existing appointments
    """

    start_time = datetime.strptime(start_time, '%I:%M %p').time()  # Convert to time object
    end_time = datetime.strptime(end_time, '%I:%M %p').time()  # Convert to time object

    # print(f"Start Time: {start_time}")
    # print(f"End Time: {end_time}")
    # Convert existing appointments to time strings for comparison
    booked_slots = [
        (appt.start_time.strftime('%H:%M'), appt.end_time.strftime('%H:%M'))
        for appt in existing_appointments
    ]
    # print(booked_slots)
    slots = []
    current_time = start_time
    while current_time < end_time:
        slot_end = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=duration)).time()
        # print(slot_end)
        slot_str = current_time.strftime('%H:%M')
        slot_end_str = slot_end.strftime('%H:%M')

        # print(slot_str, slot_end_str)
        # Check if slot is available
        is_available = True
        for booked_start, booked_end in booked_slots:
            if not (slot_end_str <= booked_start or slot_str >= booked_end):
                is_available = False
                break

        if is_available and slot_end <= end_time:
            slots.append({
                'start': slot_str,
                'end': slot_end_str,
                'display': f"{slot_str} - {slot_end_str}"
            })

        current_time = slot_end

    return slots


def get_available_slots_for_doctor(doctor_id, appointment_date):
    """
    Core logic to get available time slots for a doctor on a specific date.
    Returns a list of dictionaries, where each dict represents an available slot.
    """
    day_of_week_name = appointment_date.strftime('%A')

    days_map = {
        'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4,
        'Friday': 5, 'Saturday': 6, 'Sunday': 7
    }
    day_of_week = days_map.get(day_of_week_name)

    if day_of_week is None:
        return {'error': 'Invalid day of week'}, 400

    availability = Availability.query.filter_by(
        doctor_id=doctor_id,
        day_of_week=day_of_week
    ).first()

    if not availability:
        return {'error': 'Doctor not available on this day'}, 400

    existing_appointments = Appointment.query.filter_by(
        doctor_id=doctor_id,
        date=appointment_date
    ).all()

    slots = generate_time_slots(
        availability.from_time,
        availability.to_time,
        existing_appointments
    )
    return {'slots': slots}, 200 # Return data and status code as a tuple