import datetime

from controllers.chat_bot_controllers.utils.helper_funcation import get_chatbot_options
from models import Department, Appointment, UserRole, Patient  # Ensure Patient is imported
from models.departmentAssignmentModel import DepartmentAssignment
from models.doctorModel import Doctor
from utils.config import db
from utils.generate_time_slots import get_available_slots_for_doctor


def handle_book_appointment_start(user_obj, data, chat_context):
    """
    Handles the 'book_appointment' selection, asks for department.
    """
    bot_response_text = "Okay, let's book an appointment. First, which department would you like to visit?"
    departments = Department.query.all()
    if departments:
        bot_options = [
            {"text": dept.name, "value": f"department_{dept.id}"} for dept in departments
        ]
        bot_options.append({"text": "Go Back to Main Menu 🔙", "value": "main_menu"})
        next_state = 'select_department'
    else:
        bot_response_text = "I'm sorry, I couldn't find any departments. Please try again later or contact support."
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'

    # Initialize appointment context
    chat_context['current_appointment_request'] = {
        'department_id': None,
        'doctor_id': None,
        'appointment_date': None,
        'start_time': None,
        'reason': None,
        'treatment_ids': [],
        'patient_id': user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None,
        'requester_user_id': user_obj.id,
    }

    return bot_response_text, bot_options, next_state, chat_context


def handle_select_department(user_obj, data, chat_context):
    """
    Handles department selection and asks for doctor.
    """
    user_selection_value = data.get('selection_value')
    if user_selection_value == 'main_menu':
        return "Returning to main menu.", get_chatbot_options('main_menu_options'), 'main_menu_options', {}

    if user_selection_value.startswith('department_'):
        department_id = int(user_selection_value.split('_')[1])
        chat_context['current_appointment_request']['department_id'] = department_id

        doctors = Doctor.query \
            .join(DepartmentAssignment) \
            .filter(DepartmentAssignment.department_id == department_id) \
            .all()
        if doctors:
            bot_response_text = f"Great! Please select a doctor from the {Department.query.get(department_id).name} department:"
            bot_options = [
                {"text": f"Dr. {doc.first_name} {doc.last_name}", "value": f"doctor_{doc.id}"} for doc in doctors
            ]
            bot_options.append({"text": "Go Back to Department Selection 🔙", "value": "select_department"})
            bot_options.append({"text": "Go Back to Main Menu 🏠", "value": "main_menu"})
            next_state = 'select_doctor'
        else:
            bot_response_text = f"No doctors found in the {Department.query.get(department_id).name} department. Please choose another department."
            next_state = 'select_department'
            departments = Department.query.all()
            bot_options = [
                {"text": dept.name, "value": f"department_{dept.id}"} for dept in departments
            ]
            return bot_response_text, bot_options, next_state, chat_context
            # return handle_book_appointment_start(user_obj, data, chat_context)  # Go back to department selection
    else:
        bot_response_text = "Please select a valid department."
        return handle_book_appointment_start(user_obj, data, chat_context)

    return bot_response_text, bot_options, next_state, chat_context


def handle_select_doctor(user_obj, data, chat_context):
    """
    Handles doctor selection and asks for appointment date.
    """
    user_selection_value = data.get('selection_value')
    if user_selection_value == 'main_menu':
        return "Returning to main menu.", get_chatbot_options('main_menu_options'), 'main_menu_options', {}
    if user_selection_value == 'select_department':
        return handle_book_appointment_start(user_obj, data, chat_context)

    if user_selection_value.startswith('doctor_'):
        doctor_id = int(user_selection_value.split('_')[1])
        chat_context['current_appointment_request']['doctor_id'] = doctor_id
        doctor = Doctor.query.get(doctor_id)
        if doctor:
            chat_context['current_appointment_request']['doctor_name'] = f"Dr. {doctor.first_name} {doctor.last_name}"
            bot_response_text = f"You've selected {chat_context['current_appointment_request']['doctor_name']}. Now, what date would you like to book the appointment?"
            bot_options = get_chatbot_options('book_appointment_date_options')
            next_state = 'select_date'
        else:
            bot_response_text = "Invalid doctor selection. Please try again."
            # Go back to doctor selection for the current department
            return handle_select_department(user_obj, {
                'selection_value': f"department_{chat_context['current_appointment_request']['department_id']}"},
                                            chat_context)
    else:
        bot_response_text = "Please select a valid doctor."
        return handle_select_department(user_obj, {
            'selection_value': f"department_{chat_context['current_appointment_request']['department_id']}"},
                                        chat_context)

    return bot_response_text, bot_options, next_state, chat_context


def handle_select_date(user_obj, data, chat_context):
    """
    Handles date selection and asks for time slot.
    """
    user_selection_value = data.get('selection_value')
    current_date = datetime.date.today()
    selected_date = None

    if user_selection_value == 'main_menu':
        return "Returning to main menu.", get_chatbot_options('main_menu_options'), 'main_menu_options', {}
    if user_selection_value == 'select_department':
        return handle_book_appointment_start(user_obj, data, chat_context)

    if user_selection_value == 'today':
        selected_date = current_date
    elif user_selection_value == 'tomorrow':
        selected_date = current_date + datetime.timedelta(days=1)
    elif user_selection_value == 'pick_date':
        bot_response_text = "Please enter the desired date in YYYY-MM-DD format (e.g., 2025-12-25)."
        bot_options = [{"text": "Go Back to Date Options 🔙", "value": "select_date"},
                       {"text": "Go Back to Main Menu 🏠", "value": "main_menu"}]
        next_state = 'input_date'
        chat_context['last_state'] = 'input_date'  # Store state for direct input handling
        return bot_response_text, bot_options, next_state, chat_context
    elif data.get('message') and chat_context.get('last_state') == 'input_date':  # Handle direct date input
        try:
            selected_date = datetime.datetime.strptime(data['message'], '%Y-%m-%d').date()
            if selected_date < current_date:
                bot_response_text = "You cannot book an appointment in the past. Please enter a future date in YYYY-MM-DD format."
                bot_options = [{"text": "Go Back to Date Options 🔙", "value": "select_date"},
                               {"text": "Go Back to Main Menu 🏠", "value": "main_menu"}]
                next_state = 'input_date'
                return bot_response_text, bot_options, next_state, chat_context
        except ValueError:
            bot_response_text = "Invalid date format. Please enter the date in YYYY-MM-DD format (e.g., 2025-12-25)."
            bot_options = [{"text": "Go Back to Date Options 🔙", "value": "select_date"},
                           {"text": "Go Back to Main Menu 🏠", "value": "main_menu"}]
            next_state = 'input_date'
            return bot_response_text, bot_options, next_state, chat_context
    else:
        bot_response_text = "Please select a valid date option."
        bot_options = get_chatbot_options('book_appointment_date_options')
        next_state = 'select_date'
        return bot_response_text, bot_options, next_state, chat_context

    chat_context['current_appointment_request']['appointment_date'] = selected_date.isoformat()
    doctor_id = chat_context['current_appointment_request']['doctor_id']

    # Call the reusable utility function directly
    slots_response, status_code = get_available_slots_for_doctor(doctor_id, selected_date)

    if status_code == 200 and slots_response and 'slots' in slots_response:
        slots = slots_response['slots']
        if slots:
            bot_response_text = f"Okay, here are the available time slots for {selected_date.strftime('%Y-%m-%d')} with {chat_context['current_appointment_request']['doctor_name']}:"
            bot_options = []
            for slot in slots:
                bot_options.append({"text": slot['display'], "value": slot['start']})
            bot_options.append({"text": "Go Back to Date Selection 🔙", "value": "select_date"})
            bot_options.append({"text": "Go Back to Doctor Selection 🔙", "value": "select_doctor"})
            bot_options.append({"text": "Go Back to Main Menu 🏠", "value": "main_menu"})
            next_state = 'select_time_slot'
        else:
            bot_response_text = f"No available slots for {selected_date.strftime('%Y-%m-%d')} with {chat_context['current_appointment_request']['doctor_name']}. Please try another date or doctor."
            bot_options = get_chatbot_options('book_appointment_date_options')
            bot_options.append({"text": "Go Back to Doctor Selection 🔙", "value": "select_doctor"})
            next_state = 'select_date'
    else:
        # Handle errors from the slot retrieval function
        error_message = slots_response.get('error', 'Failed to retrieve available slots.')
        bot_response_text = f"Error: {error_message} Please try again or select a different date/doctor."
        bot_options = get_chatbot_options('book_appointment_date_options')
        bot_options.append({"text": "Go Back to Doctor Selection 🔙", "value": "select_doctor"})
        next_state = 'select_date'

    return bot_response_text, bot_options, next_state, chat_context


def handle_select_time_slot(user_obj, data, chat_context):
    """
    Handles time slot selection and asks for reason/treatments.
    """
    user_selection_value = data.get('selection_value')
    if user_selection_value == 'main_menu':
        return "Returning to main menu.", get_chatbot_options('main_menu_options'), 'main_menu_options', {}
    if user_selection_value == 'select_date':
        # Re-trigger date selection with current context
        return handle_select_date(user_obj, {
            'selection_value': chat_context['current_appointment_request']['appointment_date_option']}, chat_context)
    if user_selection_value == 'select_doctor':
        # Re-trigger doctor selection with current context
        return handle_select_doctor(user_obj, {
            'selection_value': f"doctor_{chat_context['current_appointment_request']['doctor_id']}"}, chat_context)

    # Validate if the selected time slot is valid (e.g., within fetched slots)
    # For simplicity, we'll assume valid selection for now
    chat_context['current_appointment_request']['start_time'] = user_selection_value

    bot_response_text = (
        f"You've selected {chat_context['current_appointment_request']['start_time']} on "
        f"{chat_context['current_appointment_request']['appointment_date']} with "
        f"{chat_context['current_appointment_request']['doctor_name']}.\n\n"
        "Please briefly describe the reason for your visit (e.g., 'fever and cough', 'follow-up checkup')."
    )
    bot_options = []
    next_state = 'input_reason'
    return bot_response_text, bot_options, next_state, chat_context


def handle_input_reason(user_obj, data, chat_context):
    """
    Handles reason input and asks for confirmation.
    """
    user_message = data.get('message')
    if user_message == 'main_menu':
        return "Returning to main menu.", get_chatbot_options('main_menu_options'), 'main_menu_options', {}
    if user_message == 'select_time_slot':
        return handle_select_time_slot(user_obj, {}, chat_context)  # Re-present the last options

    chat_context['current_appointment_request']['reason'] = user_message

    # Display summary for confirmation
    summary = f"Summary of your appointment:\n" \
              f"Doctor: {chat_context['current_appointment_request']['doctor_name']}\n" \
              f"Date: {chat_context['current_appointment_request']['appointment_date']}\n" \
              f"Time: {chat_context['current_appointment_request']['start_time']}\n" \
              f"Reason: {chat_context['current_appointment_request']['reason']}\n\n" \
              f"Does this look correct?"

    bot_response_text = summary
    bot_options = get_chatbot_options('book_appointment_confirm_options')
    next_state = 'confirm_appointment'
    return bot_response_text, bot_options, next_state, chat_context


def handle_confirm_appointment(user_obj, data, chat_context):
    """
    Handles final confirmation and attempts to book the appointment.
    """
    user_selection_value = data.get('selection_value')
    appointment_request = chat_context.get('current_appointment_request')
    bot_response_text = ""
    bot_options = []
    next_state = ""
    if user_selection_value == 'main_menu':
        return "Returning to main menu.", get_chatbot_options('main_menu_options'), 'main_menu_options', {}
    elif user_selection_value == 'change_details':
        # Send user back to a point to change details, e.g., doctor selection
        bot_response_text = "Okay, what would you like to change? You can select a new doctor or date."
        bot_options = [
            {"text": "Change Doctor", "value": "select_department"},
            {"text": "Change Date", "value": "select_date"},
            {"text": "Go Back to Main Menu 🏠", "value": "main_menu"},
        ]
        next_state = 'book_appointment_change_details'  # New state to handle change options
        return bot_response_text, bot_options, next_state, chat_context
    elif user_selection_value == 'cancel_appointment_booking':
        chat_context.pop('current_appointment_request', None)  # Clear context
        bot_response_text = "Appointment booking cancelled. How else can I assist you?"
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'
        return bot_response_text, bot_options, next_state, chat_context
    elif user_selection_value == 'confirm_appointment':
        if not appointment_request:
            bot_response_text = "It looks like your appointment details are missing. Please start again."
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu_options'
            return bot_response_text, bot_options, next_state, chat_context

        # Extract data needed for booking
        doctor_id = appointment_request.get('doctor_id')
        appointment_date_str = appointment_request.get('appointment_date')
        start_time_str = appointment_request.get('start_time')
        reason = appointment_request.get('reason')
        patient_id = appointment_request.get('patient_id')  # From chat_context init

        if not all([doctor_id, appointment_date_str, start_time_str, reason, patient_id]):
            bot_response_text = "Missing some details for booking. Let's restart the process."
            chat_context.pop('current_appointment_request', None)
            return handle_book_appointment_start(user_obj, data, chat_context)

        # Convert date and time strings to Python objects
        try:
            appointment_date = datetime.datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            start_time_dt = datetime.datetime.strptime(start_time_str,
                                                       '%H:%M')  # Parse to datetime object first to use timedelta
            start_time = start_time_dt.time()
            end_time = (start_time_dt + datetime.timedelta(minutes=30)).time()
        except ValueError:
            bot_response_text = "There was an issue with the date/time format. Please try again."
            return handle_select_time_slot(user_obj, data, chat_context)

        try:
            # Check if patient exists
            patient = Patient.query.get(patient_id)
            if not patient:
                bot_response_text = "Patient profile not found. Cannot book appointment."
                return "Patient profile not found. Cannot book appointment.", get_chatbot_options(
                    'main_menu_options'), 'main_menu_options', {}

            # Create new appointment object
            new_appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor_id,
                date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                reason=reason,
                status='PENDING'  # Or 'SCHEDULED' depending on your default
            )

            db.session.add(new_appointment)
            db.session.commit()

            bot_response_text = (
                f"🎉 Your appointment with {appointment_request['doctor_name']} on "
                f"{appointment_request['appointment_date']} at {appointment_request['start_time']} "
                f"has been successfully booked! Your appointment ID is **{new_appointment.id}**. "
                "You can view your appointments from the main menu."
            )
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu_options'
            chat_context.pop('current_appointment_request', None)  # Clear context after successful booking

        except Exception as e:
            db.session.rollback()
            print(f"Error booking appointment: {e}")
            import traceback
            traceback.print_exc()
            bot_response_text = "I'm sorry, an error occurred while trying to book your appointment. Please try again or contact support."
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu_options'

    return bot_response_text, bot_options, next_state, chat_context
