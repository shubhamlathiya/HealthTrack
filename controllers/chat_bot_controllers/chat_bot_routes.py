# app.py (main Flask application file)

import json
import os

from flask import jsonify, session, render_template, request
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from controllers.chat_bot_controllers import chatbot
from middleware.auth_middleware import token_required
from models import UserRole, User, Patient, Appointment, Prescription, Medicine


def load_chatbot_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Correct path: go into 'data' folder from current_dir
    config_path = os.path.join(current_dir, 'data', 'chatbot_config.json')  # <-- MODIFY THIS LINE

    # config_path = 'data/chatbot_config.json'

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _cached_chatbot_config = json.load(f)
        print(f"Chatbot configuration loaded successfully from {config_path}")
        print(f"Loaded config keys: {_cached_chatbot_config.keys()}")
        return _cached_chatbot_config
    except FileNotFoundError:
        print(
            f"ERROR: Chatbot config file NOT FOUND at {config_path}. Please ensure the file exists and the path is correct.")
        _cached_chatbot_config = {}  # Set to empty dict on failure to prevent repeated errors
        return {}  # Return empty dict so app doesn't crash immediately
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from {config_path}. Check file format for errors.")
        print(f"JSON Decoding Error: {e}")
        _cached_chatbot_config = {}
        return {}
    except Exception as e:
        print(f"An unexpected error occurred while loading chatbot config: {e}")
        print(f"Config path attempted: {config_path}")
        _cached_chatbot_config = {}
        return {}


def get_chatbot_options(key, default_options=None):
    config = load_chatbot_config()  # Ensures config is loaded

    print(f"Attempting to retrieve options for key: '{key}'")
    retrieved_options = config.get(key, default_options if default_options is not None else [])

    print(f"Options retrieved for '{key}': {retrieved_options}")
    return retrieved_options


# Helper function for quantity validation (example)
def is_valid_quantity(qty):
    return isinstance(qty, int) and qty > 0


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


def handle_medicine_request_start(user_obj, data, chat_context):
    """Handles the 'medicine_request_start' state."""
    user_selection_value = data.get('selection_value')
    patient_id = user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None
    bot_response_text = ""
    bot_options = []
    next_state = 'main_menu_options'  # Set a safe default

    if user_selection_value == 'search_by_name':
        bot_response_text = "Please type the name of the medicine you are looking for."
        next_state = 'medicine_search_input'

    elif user_selection_value == 'view_prescriptions':
        if patient_id:
            appointments = Appointment.query.filter_by(patient_id=patient_id).all()
            appointment_ids = [appointment.id for appointment in appointments]

            if not appointment_ids:
                bot_response_text = "No appointments found to base prescriptions on."
            else:
                prescriptions = Prescription.query.filter(
                    Prescription.appointment_id.in_(appointment_ids),
                    Prescription.is_deleted == False
                ).all()

                if prescriptions:
                    prescriptions_data = []
                    for prescription in prescriptions:
                        prescription_data = {
                            'id': prescription.id,
                            'appointment_date': prescription.appointment.date.isoformat() if prescription.appointment and prescription.appointment.date else None,
                            'doctor_name': f"{prescription.appointment.doctor.first_name} {prescription.appointment.doctor.last_name}" if prescription.appointment and prescription.appointment.doctor else None,
                            'notes': prescription.notes,
                            'status': prescription.status,
                            'medications': [
                                {'name': med.name, 'dosage': med.dosage, 'meal_instructions': med.meal_instructions,
                                 'timing': [t.timing for t in med.timings] if med.timings else []} for med in
                                prescription.medications]
                        }
                        prescriptions_data.append(prescription_data)

                    bot_response_text = "Here are your active prescriptions:"
                    for p_data in prescriptions_data:
                        bot_response_text += f"\n\n--- Prescription ID: {p_data['id']} ---"
                        bot_response_text += f"\nDate: {p_data['appointment_date']} with Dr. {p_data['doctor_name']}"
                        if p_data['medications']:
                            bot_response_text += "\nMedications:"
                            for med in p_data['medications']:
                                bot_response_text += f"\n  - {med['name']} ({med['dosage']}, {med['meal_instructions']} {', '.join(med['timing'])})"
                    chat_context['active_prescriptions'] = prescriptions_data
                    bot_options = [{"text": f"Select Prescription {p['id']}", "value": str(p['id'])} for p in
                                   prescriptions_data]
                    next_state = 'medicine_select_prescription'
                else:
                    bot_response_text = "No active prescriptions found."
        else:
            bot_response_text = "I cannot retrieve prescriptions without a linked patient profile."

        # Safely assign default options if needed
        if not chat_context.get('active_prescriptions'):
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu_options'

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_select_prescription(user_obj, data, chat_context):
    """Handles selecting a specific prescription for medicine request."""
    user_selection_value = data.get('selection_value')
    patient_id = user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None
    patient_address = user_obj.patient.address if user_obj.role == UserRole.PATIENT and user_obj.patient else None

    selected_prescription = next(
        (p for p in chat_context.get('active_prescriptions', []) if str(p['id']) == user_selection_value), None)

    if selected_prescription:
        # Simulate items for calculation (you'd fetch actual medicine items from DB here)
        # For simplicity, let's assume 'medications' in the context are the 'items'
        items_for_request = []
        total_prescription_amount = 0.0
        for med in selected_prescription.get('medications', []):
            # You'd need to fetch actual medicine details like unit_price from your Medicine model
            # For this example, let's assume a dummy price
            dummy_unit_price = 10.0  # Replace with actual logic to get medicine price
            quantity = 1  # You might infer quantity from dosage or have a default
            items_for_request.append({
                'medicine_name': med['name'],
                'quantity_prescribed': quantity,
                'unit_price': dummy_unit_price
            })
            total_prescription_amount += quantity * dummy_unit_price

        chat_context['current_medicine_request'] = {
            'patient_id': patient_id,
            'requester_user_id': user_obj.id,
            'delivery_address': patient_address or 'Unknown Address',
            'items': items_for_request
        }
        bot_response_text = f"Requesting all medicines from Prescription #{selected_prescription['id']}. Total estimated amount: Rs. {total_prescription_amount:.2f}."
        bot_options = [
            {"text": "Confirm Delivery", "value": "confirm_delivery"},
            {"text": "Modify Items", "value": "modify_items"},
            {"text": "Cancel Request", "value": "cancel_request"}  # Renamed for clarity
        ]
        next_state = 'medicine_delivery_confirm'
    else:
        bot_response_text = "Invalid prescription selected. Please try again."
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_quantity(user_obj, data, chat_context):
    """Handles the 'medicine_quantity' state."""
    user_selection_value = data.get('selection_value')
    current_medicine_request = chat_context.get('current_medicine_request', {})
    delivery_address = current_medicine_request.get('delivery_address', 'Unknown Address')

    if user_selection_value == 'other_quantity':
        bot_response_text = "Please type the exact quantity you need."
        next_state = 'medicine_other_quantity_input'
    elif user_selection_value:
        try:
            quantity = int(user_selection_value)
            if quantity > 0 and current_medicine_request and current_medicine_request.get('items'):
                # Assuming this is for a single item for now, extend for multiple items
                current_medicine_request['items'][0][
                    'quantity_requested'] = quantity  # Use a specific key for requested quantity
                bot_response_text = f"You selected {quantity} units. Confirm delivery address: {delivery_address}?"
                bot_options = get_chatbot_options('medicine_address_options')
                next_state = 'medicine_delivery_address'
            else:
                bot_response_text = "Invalid quantity or no medicine selected. Please select an option or type a number."
                bot_options = get_chatbot_options('medicine_quantity_options')
                next_state = 'medicine_quantity'
        except ValueError:
            bot_response_text = "Invalid quantity format. Please enter a number."
            bot_options = get_chatbot_options('medicine_quantity_options')
            next_state = 'medicine_quantity'
    else:
        bot_response_text = "Please select a quantity or type 'other_quantity'."
        bot_options = get_chatbot_options('medicine_quantity_options')
        next_state = 'medicine_quantity'

    chat_context['current_medicine_request'] = current_medicine_request  # Update context
    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_delivery_address(user_obj, data, chat_context):
    """Handles the 'medicine_delivery_address' state."""
    user_selection_value = data.get('selection_value')
    if user_selection_value == 'confirm_address':
        bot_response_text = "How would you like to pay?"
        bot_options = get_chatbot_options('medicine_payment_options')
        next_state = 'medicine_payment_method'
    elif user_selection_value == 'enter_new_address':
        bot_response_text = "Please type the new delivery address."
        next_state = 'medicine_new_address_input'
    else:
        bot_response_text = "Please confirm the address or provide a new one."
        bot_options = get_chatbot_options('medicine_address_options')
        next_state = 'medicine_delivery_address'
    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_payment_method(user_obj, data, chat_context):
    """Handles the 'medicine_payment_method' state."""
    user_selection_value = data.get('selection_value')
    if user_selection_value in [opt['value'] for opt in get_chatbot_options('medicine_payment_options')]:
        chat_context['current_medicine_request']['payment_method'] = user_selection_value.replace('_', ' ')
        bot_response_text = f"Okay, payment method: {user_selection_value.replace('_', ' ')}. Ready to place your order?"
        bot_options = get_chatbot_options('medicine_final_confirm_options')
        next_state = 'medicine_final_confirm'
    else:
        bot_response_text = "Please select a payment method."
        bot_options = get_chatbot_options('medicine_payment_options')
        next_state = 'medicine_payment_method'
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


def handle_medicine_search_input(user_obj, data, chat_context):
    """Handles the 'medicine_search_input' state."""

    search_term = data.get('message')
    bot_options = []
    next_state = 'main_menu_options'  # default fallback
    if not search_term:
        bot_response_text = "Please enter a valid medicine name or number to search."
        bot_options = get_chatbot_options('main_menu_options')
        return bot_response_text, bot_options, next_state, chat_context

    medicines = Medicine.query.filter(
        or_(
            Medicine.name.ilike(f'%{search_term}%'),
            Medicine.medicine_number.ilike(f'%{search_term}%')
        ),
        Medicine.is_deleted == False
    ).options(
        joinedload(Medicine.category),
        joinedload(Medicine.company),
        joinedload(Medicine.group),
        joinedload(Medicine.unit)
    ).limit(6).all()

    if not medicines:
        bot_response_text = f"No medicines found matching '{search_term}'."
        bot_options = get_chatbot_options('main_menu_options')
    else:
        bot_response_text = f"Found the following medicines matching '{search_term}':"
        medicine_list = []

        for med in medicines:
            med_text = f"- {med.name} (#{med.medicine_number})"
            med_text += f"\n  Category: {med.category.name if med.category else 'N/A'}"
            med_text += f"\n  Company: {med.company.name if med.company else 'N/A'}"
            med_text += f"\n  Price: ₹{float(med.default_mrp) if med.default_mrp else 'N/A'}"
            med_text += f"\n  Stock: {med.current_stock}"
            medicine_list.append(med_text)

            # Prepare selectable options (for example: to order or view more)
            bot_options.append({
                "text": f"Select {med.name}",
                "value": f"select_medicine_{med.id}"
            })

        bot_response_text += "\n\n" + "\n\n".join(medicine_list)
        next_state = 'medicine_select_from_search'
        chat_context['search_results'] = [med.id for med in medicines]  # store for later

    return bot_response_text, bot_options, next_state, chat_context


# --- State Handler Mapping ---
STATE_HANDLERS = {
    # --- Initial State ---
    'initial': handle_initial_state,

    # --- Main Menu Options ---
    'main_menu_options': handle_main_menu_options,

    # --- Medicine Request Flow ---
    'request_medicine': handle_medicine_request_start,  # Although you have medicine_request_start, aligning names helps
    'medicine_request_start': handle_medicine_request_start,
    'medicine_select_prescription': handle_medicine_select_prescription,
    'medicine_quantity': handle_medicine_quantity,
    'medicine_delivery_address': handle_medicine_delivery_address,
    'medicine_payment_method': handle_medicine_payment_method,
    'medicine_search_input': handle_medicine_search_input,


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
    current_state = data.get('conversation_state')
    chat_context = data.get('context', {})

    user_obj = User.query.filter_by(id=int(current_user)).first()
    if not user_obj:
        return jsonify({"message": "User not found or session invalid."}), 404

    # Patient profile check for patient-specific actions
    if user_obj.role == UserRole.PATIENT and not user_obj.patient:
        return jsonify({"message": "Patient profile not found. Cannot proceed with patient-specific actions."}), 400

    bot_response_text = ""
    bot_options = []
    next_state = current_state  # Default to current state, will be updated by handlers
    updated_context = chat_context  # Default to current context, will be updated by handlers

    # Handle 'menu' command globally
    if user_message and user_message.lower() == 'menu':
        bot_response_text = "Returning to main menu."
        next_state = 'main_menu_options'
        bot_options = get_chatbot_options('main_menu_options')
        updated_context = {}  # Clear context if returning to main menu for a fresh start
        return jsonify({
            "message": bot_response_text,
            "options": bot_options,
            "next_state": next_state,
            "context": updated_context
        }), 200

    # Process the current state using the handler mapping
    handler = STATE_HANDLERS.get(current_state)
    if handler:
        bot_response_text, bot_options, next_state, updated_context = handler(user_obj, data, chat_context)
    else:
        # Fallback for unhandled states
        bot_response_text = "I'm sorry, I don't know how to handle this state. Returning to main menu."
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'
        updated_context = {}  # Clear context if returning to main menu for a fresh start

    return jsonify({
        "message": bot_response_text,
        "options": bot_options,
        "next_state": next_state,
        "context": updated_context
    }), 200
