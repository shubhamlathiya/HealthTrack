import json

from flask import jsonify, session, render_template, request

from controllers.chat_bot_controllers import chatbot
from controllers.chat_bot_controllers.utils.book_appointment import handle_book_appointment_start, \
    handle_select_department, handle_select_doctor, handle_select_date, handle_select_time_slot, handle_input_reason, \
    handle_confirm_appointment, handle_book_appointment_change_details
from controllers.chat_bot_controllers.utils.call_ambulance import handle_ambulance_start, \
    handle_ambulance_other_emergency_text_input, handle_ambulance_final_confirm_options, \
    handle_ambulance_pickup_location_confirm, handle_ambulance_new_pickup_location_input, \
    handle_ambulance_verify_pickup_location, handle_check_last_ambulance_call
from controllers.chat_bot_controllers.utils.faq_help import handle_faq_help
from controllers.chat_bot_controllers.utils.helper_funcation import get_chatbot_options
from controllers.chat_bot_controllers.utils.my_health_profile import handle_my_health_profile, \
    handle_profile_update_contact_input, handle_profile_update_health_input
from controllers.chat_bot_controllers.utils.request_medicine import handle_medicine_search_input, \
    handle_medicine_request_start, handle_medicine_select_prescription, handle_medicine_item_selection, \
    handle_medicine_modify_item, handle_medicine_set_item_quantity, handle_medicine_quantity_input, \
    handle_medicine_check_status, handle_medicine_final_confirm, handle_medicine_payment_method, \
    handle_medicine_verify_new_address, handle_medicine_new_address_input, handle_medicine_delivery_address, \
    handle_medicine_cancel_specific_order
from middleware.auth_middleware import token_required
from models import UserRole, User, Patient, Appointment, MedicineRequestStatus
from utils.config import db


@chatbot.route('/', methods=['GET'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def chatbot_page(current_user):
    return render_template("chat_bot/chat_bot.html")

@chatbot.route('/api/me', methods=['GET'])
@token_required(allowed_roles=[UserRole.PATIENT.name])
def get_user_info(current_user):
    user_id_in_session = session.get('user_id')
    user_role_in_session = session.get('role')
    print("shubham",user_id_in_session, user_role_in_session)
    if not user_id_in_session:
        return jsonify({'message': 'Unauthorized: No active session found.'}), 401

    # 2. Retrieve user from the database based on session ID
    user = User.query.filter_by(id=int(user_id_in_session)).first()

    if not user:
        print(f"Error: User with ID {user_id_in_session} not found in DB despite session.")
        session.clear()  # Clear potentially stale session data
        return jsonify({'message': 'User not found or session invalid. Please log in again.'}), 404

    if user.role.name != user_role_in_session:
        print(
            f"Warning: Session role '{user_role_in_session}' does not match DB role '{user.role.name}' for user {user.id}.")

    patient_id, name = None, None
    # Assuming 'patient' is a relationship on the User model
    if user.role == UserRole.PATIENT and hasattr(user, 'patient') and user.patient:
        patients = Patient.query.filter_by(user_id=user_id_in_session).first()
        patient_id = patients.id
        name = f"{patients.first_name} {patients.last_name}"
    # 4. Return user information
    return jsonify({
        'user_id': user.id,
        'user_role': user.role.value,  # Use .value for the string representation of the Enum
        'email': user.email,
        'patient_id': patient_id,
        'name': name,
        'is_authenticated': True
    }), 200

# --- State Handler Functions ---
def handle_initial_state(user_obj, data, chat_context):
    """Handles the 'initial' conversation state."""
    bot_response_text = f"How can I assist you today?"
    bot_options = get_chatbot_options('main_menu_options')
    next_state = 'main_menu_options'
    return bot_response_text, bot_options, next_state, chat_context


# --- Main Menu Options ---
def handle_main_menu_options(user_obj, data, chat_context):
    """Handles selections from the 'main_menu_options' state."""
    user_selection_value = data.get('selection_value')
    patient_id = user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None
    patient_address = user_obj.patient.address if user_obj.role == UserRole.PATIENT and user_obj.patient else None

    if user_selection_value == 'request_medicine':
        bot_response_text = "Okay, I can help you with that. How would you like to select your medicine?"
        bot_options = get_chatbot_options('medicine_request_options')
        next_state = 'medicine_request_start'
    elif user_selection_value == 'call_ambulance':
        bot_response_text = (
            "🚨 What type of emergency are you experiencing?\n"
            "Please select one from the options below 👇"
        )

        bot_options = get_chatbot_options('ambulance_emergency_options')
        next_state = 'ambulance_start'
        chat_context['current_ambulance_request'] = {
            'pickup_location': patient_address or 'Unknown Address',
            'patient_id': patient_id,
        }
    elif user_selection_value == 'view_appointments':
        bot_response_text = ""
        if patient_id:
            appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
                Appointment.date.desc()).limit(3).all()
            if appointments:
                bot_response_text = "Here are your upcoming appointments:"
                for appt in appointments:
                    date_str = appt.date.strftime("%Y-%m-%d") if appt.date else "N/A"
                    time_str = appt.start_time.strftime("%H:%M") if appt.start_time else "N/A"
                    doctor_name = appt.doctor.first_name if appt.doctor else "N/A"
                    bot_response_text += f"\n- On {date_str} at {time_str} with Dr. {doctor_name} (Status: {appt.status})"
            else:
                bot_response_text = "You don't have any appointments scheduled."
        else:
            bot_response_text = "I cannot retrieve appointments without a linked patient profile."

        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'
    elif user_selection_value == 'book_appointment':  # NEW: Route to appointment booking
        return handle_book_appointment_start(user_obj, data, chat_context)
    elif user_selection_value == 'my_health_profile':
        return handle_my_health_profile(user_obj, data, chat_context)
    elif user_selection_value == 'faq_help':
        return handle_faq_help(user_obj, data, chat_context)
    else:
        bot_response_text = f"You selected '{user_selection_value}'. This feature is currently under development."
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'

    return bot_response_text, bot_options, next_state, chat_context




# --- State Handler Mapping ---
STATE_HANDLERS = {
    # --- Initial State ---
    'initial': handle_initial_state,

    # --- Main Menu Options ---
    'main_menu_options': handle_main_menu_options,

    # --- Medicine Request Flow ---
    'request_medicine': handle_medicine_request_start,
    'medicine_request_start': handle_medicine_request_start,
    'medicine_select_prescription': handle_medicine_select_prescription,
    'medicine_item_selection': handle_medicine_item_selection,
    'medicine_modify_item': handle_medicine_modify_item,  # NEW
    'medicine_set_item_quantity': handle_medicine_set_item_quantity,
    # Can be streamlined with handle_medicine_modify_item
    'medicine_quantity_input': handle_medicine_quantity_input,
    'medicine_search_input': handle_medicine_search_input,
    'medicine_delivery_address': handle_medicine_delivery_address,
    'medicine_new_address_input': handle_medicine_new_address_input,
    'medicine_verify_new_address': handle_medicine_verify_new_address,
    'medicine_payment_method': handle_medicine_payment_method,
    'medicine_final_confirm': handle_medicine_final_confirm,
    'medicine_check_status': handle_medicine_check_status,  # NEW
    'medicine_cancel_specific_order': handle_medicine_cancel_specific_order,

    # --- Appointment Booking Flow --- # NEW SECTION
    'book_appointment_start': handle_book_appointment_start,
    'select_department': handle_select_department,
    'select_doctor': handle_select_doctor,
    'select_date': handle_select_date,
    'input_date': handle_select_date,  # For handling direct date input
    'select_time_slot': handle_select_time_slot,
    'input_reason': handle_input_reason,
    'confirm_appointment': handle_confirm_appointment,
    'book_appointment_change_details': handle_book_appointment_change_details,

    # --- Ambulance Request Flow ---
    'ambulance_start': handle_ambulance_start,
    'ambulance_other_emergency_text_input': handle_ambulance_other_emergency_text_input,
    'ambulance_pickup_location_confirm': handle_ambulance_pickup_location_confirm,
    'ambulance_new_pickup_location_input': handle_ambulance_new_pickup_location_input,
    'ambulance_verify_pickup_location': handle_ambulance_verify_pickup_location,
    'ambulance_final_confirm': handle_ambulance_final_confirm_options,
    'check_last_ambulance_call': handle_check_last_ambulance_call,

    # ---My Health Profile Flow ---
    'my_health_profile': handle_my_health_profile,
    'profile_update_contact_input': handle_profile_update_contact_input,
    'profile_update_health_input': handle_profile_update_health_input,

    # ---FAQs / Help Flow ---
    'faq_help': handle_faq_help,
}


# --- Main Chatbot Interact Function ---
@chatbot.route('/api/chatbot_interact', methods=['POST'], endpoint='chatbot_interact')
@token_required(
    allowed_roles=[UserRole.PATIENT.name, UserRole.DOCTOR.name, UserRole.STAFF.name])
def chatbot_interact(current_user):
    data = request.get_json()
    user_message = data.get('message')
    conversation_state_from_frontend = data.get('conversation_state')
    user_selection_value = data.get('selection_value')  # Extract selection_value here for handlers

    # --- Start Transaction ---
    try:
        # 1. Load the User object from the database using the ID from token_required
        user_obj = User.query.filter_by(id=int(current_user)).first()
        if not user_obj:
            return jsonify({"message": "User not found or session invalid."}), 404

        # Patient profile check for patient-specific actions
        if user_obj.role == UserRole.PATIENT and not user_obj.patient:
            return jsonify({"message": "Patient profile not found. Cannot proceed with patient-specific actions."}), 400

        # 2. Load persisted chat_context from the user_obj (Database is the source of truth)
        if user_obj.chat_context_json:
            chat_context = json.loads(user_obj.chat_context_json)
        else:
            chat_context = {}  # Initialize empty if no context exists

        print(f"DEBUG: Chat context loaded from DB (start of request): {chat_context}")

        # 3. Ensure 'current_medicine_request' is always initialized in the context
        # This is vital for consistency across all handlers
        chat_context.setdefault('current_medicine_request', {
            'items': [],
            'status': MedicineRequestStatus.PENDING.value,
            'patient_id': user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None,
            'requester_user_id': user_obj.id,
            'delivery_address': user_obj.patient.address if user_obj.role == UserRole.PATIENT and user_obj.patient else None,
        })

        # Optionally, update specific context fields from frontend payload if intended
        # Be careful not to override backend-managed state like 'items'
        frontend_context_data = data.get('context', {})
        if frontend_context_data.get('currentPatientAge') is not None:
            chat_context['currentPatientAge'] = frontend_context_data['currentPatientAge']
        if frontend_context_data.get('currentPatientAddress') is not None:
            chat_context['currentPatientAddress'] = frontend_context_data['currentPatientAddress']

        bot_response_text = ""
        bot_options = []
        # Determine the effective current state for the handler dispatch
        # Prioritize frontend state for explicit transitions, otherwise use a default
        effective_current_state = conversation_state_from_frontend if conversation_state_from_frontend else 'main_menu_options'  # Use main_menu_options as a safe fallback

        # Handle 'menu' command globally before dispatching to specific handlers
        if user_message and user_message.lower() == 'menu':
            bot_response_text = "Returning to main menu."
            next_state = 'main_menu_options'
            bot_options = get_chatbot_options('main_menu_options')
            updated_context = {}  # Clear context for a fresh start, including current_medicine_request
            # Re-initialize current_medicine_request after clearing if needed for the fresh state
            updated_context.setdefault('current_medicine_request', {
                'items': [],
                'status': MedicineRequestStatus.PENDING.value,
                'patient_id': user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None,
                'requester_user_id': user_obj.id,
                'delivery_address': user_obj.patient.address if user_obj.role == UserRole.PATIENT and user_obj.patient else None,
            })
        else:
            # Dispatch to the appropriate handler
            handler = STATE_HANDLERS.get(effective_current_state,
                                         handle_initial_state)  # Fallback to handle_initial_state
            # Pass the loaded chat_context to the handler
            bot_response_text, bot_options, next_state, updated_context = handler(user_obj, data, chat_context)

        # 4. Save the updated_context back to the user_obj (Database is the source of truth)
        user_obj.chat_context_json = json.dumps(updated_context)
        db.session.add(user_obj)  # Add user_obj to the session
        db.session.commit()  # Commit changes to the database

        print(f"DEBUG: Chat context committed to DB (end of request): {user_obj.chat_context_json}")

        return jsonify({
            "message": bot_response_text,
            "options": bot_options,
            "next_state": next_state,
            "context": updated_context  # Send updated context back to frontend
        }), 200

    except Exception as e:
        # 5. Handle errors gracefully and rollback the transaction
        db.session.rollback()
        print(f"ERROR in chatbot_interact: {e}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging

        return jsonify({
            "message": "Oops! Something went wrong on our end. Please try again later.",
            "options": get_chatbot_options('main_menu_options'),  # Offer main menu options as recovery
            "next_state": 'main_menu_options',
            "context": {}  # Clear context on client to prevent lingering bad state
        }), 500  # Internal Server Error
