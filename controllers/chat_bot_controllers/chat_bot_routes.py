import json

from flask import jsonify, session, render_template, request

from controllers.chat_bot_controllers import chatbot
from controllers.chat_bot_controllers.utils.helper_funcation import get_chatbot_options
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
    bot_response_text = f"Hello {user_obj.role.value}! How can I assist you today?"
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
        bot_response_text = "I'm dispatching an ambulance for you. Please confirm your current location and the nature of the emergency."
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
                Appointment.date.desc()).all()
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
    else:
        bot_response_text = f"You selected '{user_selection_value}'. This feature is currently under development."
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'

    return bot_response_text, bot_options, next_state, chat_context


def handle_ambulance_start(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    user_message = data.get('message')  # Get raw typed message

    bot_response_text = ""
    bot_options = []  # Default options for this state
    next_state = 'ambulance_start'  # Stay in this state by default if input is unclear

    current_ambulance_request = chat_context.get('current_ambulance_request', {})

    # Prioritize user selection, but fall back to message if no selection
    if user_selection_value:
        selected_emergency_text = get_chatbot_options('ambulance_emergency_options', user_selection_value)

        if user_selection_value == 'other_emergency':
            bot_response_text = "Please describe the emergency in more detail. For example: 'My leg is broken' or 'My child has a high fever'."
            next_state = 'ambulance_other_emergency_text_input'
        elif user_selection_value in ['chest_pain', 'accident', 'breathing_difficulty']:
            current_ambulance_request['emergency_description'] = selected_emergency_text
            bot_response_text = (
                f"You've indicated a  emergency. "
                f"Confirm dispatch to ?"
            )
            bot_options = get_chatbot_options('ambulance_final_confirm_options')
            next_state = 'ambulance_final_confirm'
        else:

            bot_response_text = "I'm sorry, I don't recognize that emergency type. Please choose from the options or select 'Other Emergency'."

    elif user_message and user_message.strip():

        current_ambulance_request['emergency_description'] = user_message.strip()
        bot_response_text = (
            f"You've described the emergency as: '{user_message.strip()}'. "
            f"Confirm dispatch to {current_ambulance_request['pickup_location']}?"
        )
        bot_options = get_chatbot_options('ambulance_final_confirm_options')
        next_state = 'ambulance_final_confirm'
    else:
        bot_response_text = "What is the nature of the emergency? Please select an option below, or type your emergency."

    chat_context['current_ambulance_request'] = current_ambulance_request
    return bot_response_text, bot_options, next_state, chat_context


def handle_ambulance_other_emergency_text_input(user_obj, data, chat_context):
    """
    Handles the state where the user provides a free-form text description
    for an 'Other Emergency'.
    """
    user_message = data.get('message')  # This state primarily expects text input

    bot_response_text = ""
    bot_options = []
    next_state = 'ambulance_other_emergency_text_input'  # Stay here if input is not received

    current_ambulance_request = chat_context.get('current_ambulance_request', {})

    if user_message and user_message.strip():
        current_ambulance_request['emergency_description'] = user_message.strip()
        bot_response_text = (
            f"You've described the emergency as: '{user_message.strip()}'. "
            f"Confirm dispatch to {current_ambulance_request.get('pickup_location', 'your address')}?"
        )
        bot_options = get_chatbot_options('ambulance_final_confirm_options')
        next_state = 'ambulance_final_confirm'
    else:
        bot_response_text = "Please describe the emergency in detail so I can proceed. If you wish to cancel, type 'cancel'."
        bot_options = []  # No specific options, but consider a "Cancel" option if you want
        # next_state remains ambulance_other_emergency_text_input to await valid text

    chat_context['current_ambulance_request'] = current_ambulance_request
    return bot_response_text, bot_options, next_state, chat_context


def handle_ambulance_final_confirm_options(user_obj, data, chat_context):
    """
    Handles the final confirmation or cancellation of an ambulance request.
    """
    user_selection_value = data.get('selection_value')
    # Use updated_context here as it's passed from the main chatbot_interact function
    updated_context = chat_context

    bot_response_text = ""
    bot_options = []
    next_state = 'main_menu_options'  # Default next state

    current_ambulance_request = updated_context.get('current_ambulance_request', {})

    if user_selection_value == 'confirm_dispatch':
        # --- Dispatch Logic Here ---
        # 1. Log the request: Save current_ambulance_request to your database (e.g., AmbulanceRequest model)
        #    Example: AmbulanceRequest.create(
        #        patient_id=current_ambulance_request['patient_id'],
        #        location=current_ambulance_request['pickup_location'],
        #        emergency_type=current_ambulance_request['emergency_description'],
        #        status='Dispatched'
        #    )
        # 2. Integrate with external dispatch system (if applicable).
        # 3. Notify relevant personnel.
        # ---------------------------

        emergency_description = current_ambulance_request.get('emergency_description', 'an emergency')
        pickup_location = current_ambulance_request.get('pickup_location', 'your registered address')

        bot_response_text = (
            f"Ambulance dispatched! An ambulance is on its way to {pickup_location} for {emergency_description}. "
            "Stay calm. We've notified emergency services. "
            "Please await further instructions or a call from our team."
        )
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'initial'  # Go back to the very start of the conversation flow
        updated_context = {}  # Clear context after successful request completion

    elif user_selection_value == 'cancel_ambulance':
        bot_response_text = "Ambulance request cancelled. Is there anything else I can help you with?"
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'  # Go back to main menu
        updated_context = {}  # Clear context after cancellation

    else:
        bot_response_text = "I didn't understand your selection. Please choose to confirm or cancel your ambulance request."
        bot_options = get_chatbot_options('ambulance_final_confirm_options')
        next_state = 'ambulance_final_confirm'  # Stay in this state to re-prompt

    # Return updated_context which might have been cleared or modified
    return bot_response_text, bot_options, next_state, updated_context



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
    'medicine_cancel_specific_order': handle_medicine_cancel_specific_order,  # NEW


    # --- Ambulance Request Flow ---
    'ambulance_start': handle_ambulance_start,
    'ambulance_other_emergency_text_input': handle_ambulance_other_emergency_text_input,  # NEW!
    'ambulance_final_confirm': handle_ambulance_final_confirm_options,  # Ensure this key matches next_state values

    # 'ambulance_emergency_input': handle_ambulance_emergency_input,

    # 'medicine_select_from_search':handle_medicine_select_from_search,
    # Add handlers for all other states as you implement them
    # For example: 'medicine_search_input', 'medicine_other_quantity_input', etc.
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
