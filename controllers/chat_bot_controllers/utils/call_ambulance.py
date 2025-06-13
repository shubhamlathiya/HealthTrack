import traceback

from controllers.chat_bot_controllers.utils.helper_funcation import get_chatbot_options
from models import UserRole
from models.ambulanceModel import AmbulanceRequestStatus, AmbulanceRequest
from utils.config import db


def handle_ambulance_start(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = []
    next_state = 'ambulance_start'

    if 'current_ambulance_request' not in chat_context or user_selection_value == 'request_ambulance':
        chat_context['current_ambulance_request'] = {
            'requester_user_id': user_obj.id if user_obj and hasattr(user_obj, 'id') else None,  # Safely get user ID
            'patient_id': user_obj.patient.id if user_obj and user_obj.role == UserRole.PATIENT and user_obj.patient else None,
            'pickup_location': user_obj.patient.address if user_obj and user_obj.role == UserRole.PATIENT and user_obj.patient else None,
            'emergency_description': None,
            'status': AmbulanceRequestStatus.PENDING.value  # Initial status
        }
        current_pickup_location_initial = chat_context['current_ambulance_request']['pickup_location']
        if not current_pickup_location_initial or current_pickup_location_initial.lower() == "unknown address":
            bot_response_text = "Before we proceed, please provide the pickup location for the ambulance."
            bot_options = []
            next_state = 'ambulance_new_pickup_location_input'
            return bot_response_text, bot_options, next_state, chat_context

    if user_selection_value and user_selection_value != 'request_ambulance':  # Exclude initial button click to enter this state
        emergency_type = user_selection_value

        if emergency_type == 'other_emergency':
            chat_context['current_ambulance_request']['emergency_description'] = 'Other Emergency'
            bot_response_text = "Please describe your emergency in detail:"
            bot_options = []
            next_state = 'ambulance_other_emergency_text_input'
        elif emergency_type == 'check_last_ambulance_call':
            return handle_check_last_ambulance_call(user_obj, data, chat_context)
        else:
            chat_context['current_ambulance_request']['emergency_description'] = emergency_type.replace('_',
                                                                                                        ' ').title()
            bot_response_text = f"You selected: **{chat_context['current_ambulance_request']['emergency_description']}**."
            return handle_ambulance_pickup_location_confirm(user_obj, data, chat_context)  # Transition to next step

    else:
        bot_response_text = "What type of emergency is it?"
        bot_options = get_chatbot_options('ambulance_emergency_options')
        next_state = 'ambulance_start'  # Stay in this state until a type is selected

    return bot_response_text, bot_options, next_state, chat_context


def handle_ambulance_other_emergency_text_input(user_obj, data, chat_context):
    user_message = data.get('message')
    bot_response_text = ""
    bot_options = []

    current_ambulance_request = chat_context.get('current_ambulance_request', {})

    if user_message and user_message.strip():
        current_ambulance_request['emergency_description'] = user_message.strip()
        chat_context['current_ambulance_request'] = current_ambulance_request

        bot_response_text = f"Emergency described as: **{user_message.strip()}**."
        return handle_ambulance_pickup_location_confirm(user_obj, data, chat_context)
    else:
        bot_response_text = "Please provide a description of your emergency."
        bot_options = []
        next_state = 'ambulance_other_emergency_text_input'  # Stay in this state

    return bot_response_text, bot_options, next_state, chat_context


def handle_ambulance_pickup_location_confirm(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    current_ambulance_request = chat_context.get('current_ambulance_request', {})
    bot_response_text = ""
    bot_options = get_chatbot_options('ambulance_pickup_location_options')
    next_state = 'ambulance_pickup_location_confirm'

    current_pickup_location = current_ambulance_request.get('pickup_location')

    if not current_pickup_location or current_pickup_location.lower() == "unknown address":
        bot_response_text = "Please provide the pickup location for the ambulance."
        bot_options = []  # No options if no default address to confirm
        next_state = 'ambulance_new_pickup_location_input'  # Force new input if no address
        return bot_response_text, bot_options, next_state, chat_context

    if user_selection_value == 'confirm_current_location':
        bot_response_text = f"Pickup location confirmed: **{current_pickup_location}**."
        bot_response_text += f"\n\nEmergency: **{current_ambulance_request.get('emergency_description', 'Not Specified')}**."
        bot_response_text += "\n\nLooks good? Confirm dispatch or cancel."
        bot_options = get_chatbot_options('ambulance_final_confirm_options')
        next_state = 'ambulance_final_confirm'

    elif user_selection_value == 'enter_new_pickup_address':
        bot_response_text = "Please type the new pickup location."
        bot_options = []  # Expecting text input
        next_state = 'ambulance_new_pickup_location_input'
    else:
        bot_response_text = f"The ambulance pickup location is set to: **{current_pickup_location}**. Is this correct?"

    return bot_response_text, bot_options, next_state, chat_context


def handle_ambulance_new_pickup_location_input(user_obj, data, chat_context):
    user_message = data.get('message')
    bot_response_text = ""
    bot_options = []
    next_state = 'ambulance_verify_pickup_location'  # Default to verification

    current_ambulance_request = chat_context.get('current_ambulance_request', {})

    if user_message and user_message.strip():
        current_ambulance_request['pickup_location'] = user_message.strip()
        chat_context['current_ambulance_request'] = current_ambulance_request

        bot_response_text = f"You entered: **{user_message.strip()}**. Is this correct?"
        bot_options = get_chatbot_options('ambulance_verify_pickup_options')
    else:
        bot_response_text = "Please type the pickup location."
        bot_options = []
        next_state = 'ambulance_new_pickup_location_input'  # Stay in this state

    return bot_response_text, bot_options, next_state, chat_context


def handle_ambulance_verify_pickup_location(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = []

    current_ambulance_request = chat_context.get('current_ambulance_request', {})
    confirmed_address = current_ambulance_request.get('pickup_location')

    if user_selection_value == 'pickup_address_correct':
        if confirmed_address:
            bot_response_text = f"Pickup location confirmed: **{confirmed_address}**."
            bot_response_text += f"\n\nEmergency: **{current_ambulance_request.get('emergency_description', 'Not Specified')}**."
            bot_response_text += "\n\nLooks good? Confirm dispatch or cancel."
            bot_options = get_chatbot_options('ambulance_final_confirm_options')
            next_state = 'ambulance_final_confirm'
        else:
            bot_response_text = "No address to confirm. Please enter the pickup location."
            bot_options = []
            next_state = 'ambulance_new_pickup_location_input'

    elif user_selection_value == 'pickup_address_reenter':
        bot_response_text = "Please re-enter the correct pickup location."
        bot_options = []
        next_state = 'ambulance_new_pickup_location_input'
    else:
        bot_response_text = f"You entered: **{confirmed_address}**. Is this correct?"
        bot_options = get_chatbot_options('ambulance_verify_pickup_options')
        next_state = 'ambulance_verify_pickup_location'

    return bot_response_text, bot_options, next_state, chat_context


def handle_ambulance_final_confirm_options(user_obj, data, chat_context):
    # print("shubham chat_context (entry):", chat_context) # Keep this for debugging
    user_selection_value = data.get('selection_value')
    current_ambulance_request_data = chat_context.get('current_ambulance_request', {})
    bot_response_text = ""
    bot_options = get_chatbot_options('main_menu_options')  # Default to main menu options
    next_state = 'main_menu_options'  # Default to main menu

    requester_id_from_context = current_ambulance_request_data.get('requester_user_id')
    patient_id_from_context = current_ambulance_request_data.get('patient_id')
    pickup_location_from_context = current_ambulance_request_data.get('pickup_location')
    emergency_description_from_context = current_ambulance_request_data.get('emergency_description')

    if user_selection_value == 'confirm_dispatch':
        final_requester_id = requester_id_from_context
        if final_requester_id is None:
            if user_obj and user_obj.id:
                final_requester_id = user_obj.id
                current_ambulance_request_data['requester_user_id'] = final_requester_id
            else:
                bot_response_text = "Your user ID could not be identified to place the request. Please try logging in again or contact support."
                next_state = 'main_menu_options'
                return bot_response_text, bot_options, next_state, chat_context

        if not emergency_description_from_context or not pickup_location_from_context:
            bot_response_text = "Missing emergency details or pickup location. Please restart the request."
            next_state = 'ambulance_start'  # Go back to start of ambulance flow
            bot_options = get_chatbot_options('ambulance_emergency_options')
            return bot_response_text, bot_options, next_state, chat_context

        try:
            # print("shubham final_requester_id:", final_requester_id) # This should now print the actual ID or None before the error
            new_ambulance_request = AmbulanceRequest(
                requester_user_id=final_requester_id,  # Use the validated variable
                patient_id=patient_id_from_context,  # Use the variable
                pickup_location=pickup_location_from_context,  # Use the variable
                emergency_description=emergency_description_from_context,  # Use the variable
                status=AmbulanceRequestStatus.PENDING  # Always start as PENDING
            )
            db.session.add(new_ambulance_request)
            db.session.commit()

            bot_response_text = (
                f"Ambulance request placed successfully for: **{new_ambulance_request.emergency_description}** "
                f"at **{new_ambulance_request.pickup_location}**.\n"
                f"Your request ID is **{new_ambulance_request.id}**. An ambulance will be dispatched shortly."
            )
            chat_context.pop('current_ambulance_request', None)

        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            print(f"Error placing ambulance request: {e}")
            bot_response_text = "There was an error placing your ambulance request. Please try again later or contact support."

    elif user_selection_value == 'cancel_ambulance':
        bot_response_text = "Your ambulance request has been cancelled. Is there anything else I can help you with?"
        chat_context.pop('current_ambulance_request', None)  # Clear request from context
    else:
        bot_response_text = "Invalid option. Please confirm dispatch or cancel the request."
        bot_options = get_chatbot_options('ambulance_final_confirm_options')
        next_state = 'ambulance_final_confirm'  # Stay in this state

    return bot_response_text, bot_options, next_state, chat_context


def handle_check_last_ambulance_call(user_obj, data, chat_context):
    bot_response_text = ""
    bot_options = get_chatbot_options('main_menu_options')  # Default options after showing status
    next_state = 'main_menu_options'  # Default next state

    if not user_obj or not user_obj.id:
        bot_response_text = "I cannot retrieve your past requests without a valid user profile."
        return bot_response_text, bot_options, next_state, chat_context

    last_request = AmbulanceRequest.query.filter_by(
        requester_user_id=user_obj.id
    ).order_by(
        AmbulanceRequest.request_time.desc()  # Order by most recent request time
    ).first()

    if last_request:
        bot_response_text = (
            f"Your Last Ambulance Request (ID: {last_request.id}):\n"
            f"Emergency: **{last_request.emergency_description if last_request.emergency_description else 'N/A'}**\n"
            f"Pickup Location: **{last_request.pickup_location if last_request.pickup_location else 'N/A'}**\n"
            f"Status: **{last_request.status.value.upper()}**\n"
            f"Requested On: **{last_request.request_time.strftime('%Y-%m-%d %H:%M:%S')}**"
        )
        if last_request.assigned_ambulance:
            bot_response_text += f"\nAssigned Ambulance: {last_request.assigned_ambulance.driver_name} (License: {last_request.assigned_ambulance.license_plate})"
        bot_response_text += "\n\nWhat would you like to do next?"
    else:
        bot_response_text = "You don't have any past ambulance requests with us. What would you like to do?"

    next_state = 'main_menu_options'

    return bot_response_text, bot_options, next_state, chat_context
