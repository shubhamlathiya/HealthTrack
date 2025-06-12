# app.py (main Flask application file)

import json
import os

from flask import jsonify, session, render_template, request

from controllers.chat_bot_controllers import chatbot
from middleware.auth_middleware import token_required
from models import UserRole, User, Patient, Appointment, Prescription


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


@chatbot.route("/api/view-appointment", methods=['GET'], endpoint="view_appointment")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def view_appointment(current_user):  # current_user is expected to be the user's ID by your query
    # Find the patient associated with the current user ID
    patient = Patient.query.filter_by(user_id=current_user).first()

    if not patient:
        return jsonify({"message": "Patient profile not found for this user."}), 404

    # Fetch appointments for the found patient, ordered by date descending
    appointments = Appointment.query.filter_by(
        patient_id=patient.id
    ).order_by(
        Appointment.date.desc()
    ).all()

    # Prepare the data for JSON response
    appointment_list = []
    if appointments:
        for appt in appointments:
            appointment_data = {
                "id": appt.id,
                "date": appt.date.strftime("%Y-%m-%d") if appt.date else None,
                "time": appt.time.strftime("%H:%M") if appt.time else None,  # Assuming 'time' is a time object
                "status": appt.status,
                "doctor_name": appt.doctor.name if appt.doctor else "N/A",  # Assuming appt.doctor exists and has a name
                "department": appt.department.name if appt.department else "N/A",  # Assuming appt.department exists
                "notes": appt.notes
                # Add any other relevant fields you want to expose
            }
            appointment_list.append(appointment_data)

    # You can also include patient info if needed by the chatbot
    patient_info = {
        "id": patient.id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "address": patient.address
        # Add other patient details if relevant
    }

    # Return the data as a JSON response
    return jsonify({
        "message": "Appointments retrieved successfully.",
        "patient": patient_info,
        "appointments": appointment_list
    }), 200


@chatbot.route('/api/chatbot_interact', methods=['POST'], endpoint='chatbot_interact')
@token_required(
    allowed_roles=[UserRole.PATIENT.name, UserRole.DOCTOR.name, UserRole.STAFF.name])  # Adjust roles as needed
def chatbot_interact(current_user):
    data = request.get_json()
    user_message = data.get('message')
    user_selection_value = data.get('selection_value')
    current_state = data.get('conversation_state')
    chat_context = data.get('context', {})

    user_obj = User.query.filter_by(id=int(current_user)).first()
    if not user_obj:
        return jsonify({"message": "User not found or session invalid."}), 404

    patient_id = None
    patient_address = None
    if user_obj.role == UserRole.PATIENT and user_obj.patient:
        patient_id = user_obj.patient.id
        patient_address = user_obj.patient.address
    elif user_obj.role == UserRole.PATIENT and not user_obj.patient:
        return jsonify({"message": "Patient profile not found. Cannot proceed with patient-specific actions."}), 400

    bot_response_text = ""
    bot_options = []
    next_state = current_state
    updated_context = chat_context

    if current_state == 'initial':
        bot_response_text = f"Hello {user_obj.role.value}! How can I assist you today?"
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'

    elif current_state == 'main_menu_options':
        if user_selection_value == 'request_medicine':
            bot_response_text = "Okay, I can help you with that. How would you like to select your medicine?"
            bot_options = get_chatbot_options('medicine_request_options')
            next_state = 'medicine_request_start'
        elif user_selection_value == 'call_ambulance':
            bot_response_text = "I'm dispatching an ambulance for you. Please confirm your current location and the nature of the emergency."
            bot_options = get_chatbot_options(
                'ambulance_emergency_options')  # Initial options, then address confirmation
            next_state = 'ambulance_start'
            updated_context['current_ambulance_request'] = {
                'pickup_location': patient_address or 'Unknown Address',
                'patient_id': patient_id,
            }
        elif user_selection_value == 'view_appointments':
            appointments_data = []
            if patient_id:
                appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
                    Appointment.date.desc()).all()
                if appointments:
                    for appt in appointments:
                        appointments_data.append({
                            "id": appt.id,
                            "date": appt.date.strftime("%Y-%m-%d") if appt.date else None,
                            "time": appt.time.strftime("%H:%M") if appt.time else None,
                            "status": appt.status,
                            "doctor_name": appt.doctor.name if appt.doctor else "N/A",
                            "department": appt.department.name if appt.department else "N/A",
                            "notes": appt.notes
                        })
                    bot_response_text = "Here are your upcoming appointments:"
                    for appt in appointments_data:
                        bot_response_text += f"\n- On {appt['date']} at {appt['time']} with Dr. {appt['doctor_name']} (Status: {appt['status']})"
                else:
                    bot_response_text = "You don't have any appointments scheduled."
            else:
                bot_response_text = "I cannot retrieve appointments without a linked patient profile."

            bot_options = get_chatbot_options('main_menu_options')  # Always return to main menu after action
            next_state = 'main_menu'
        # ... continue with other main menu options, using get_chatbot_options
        else:
            bot_response_text = f"You selected '{user_selection_value}'. This feature is currently under development."
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu'

    # ... (Rest of your conversation states, replacing hardcoded options with get_chatbot_options) ...

    elif current_state == 'medicine_request_start':
        if user_selection_value == 'search_by_name':
            bot_response_text = "Please type the name of the medicine you are looking for."
            next_state = 'medicine_search_input'
        elif user_selection_value == 'view_prescriptions':
            prescriptions_data = []
            bot_response_text = ""
            if patient_id:
                # You can directly call the logic from view_patient_prescriptions here
                # Or, if this were a separate, internal function, call it.
                # For simplicity and directness, let's embed the relevant parts:
                appointments = Appointment.query.filter_by(patient_id=patient_id).all()
                appointment_ids = [appointment.id for appointment in appointments]

                if not appointment_ids:
                    bot_response_text = f"No appointments found for to base prescriptions on."
                else:
                    prescriptions = Prescription.query.filter(
                        Prescription.appointment_id.in_(appointment_ids),
                        Prescription.is_deleted == False
                    ).all()

                    if prescriptions:
                        for prescription in prescriptions:
                            # Build prescription_data dictionary as done in the dedicated route
                            prescription_data = {
                                'id': prescription.id,
                                'appointment_id': prescription.appointment_id,
                                'appointment_date': prescription.appointment.date.isoformat() if prescription.appointment and prescription.appointment.date else None,
                                'doctor_name': f"{prescription.appointment.doctor.first_name} {prescription.appointment.doctor.last_name}" if prescription.appointment and prescription.appointment.doctor else None,
                                'notes': prescription.notes,
                                'status': prescription.status,
                                'created_at': prescription.created_at.isoformat() if prescription.created_at else None,
                                'medications': [],
                                'test_reports': []
                            }
                            for med in prescription.medications:
                                prescription_data['medications'].append({
                                    'name': med.name, 'dosage': med.dosage,
                                    'meal_instructions': med.meal_instructions,
                                    'timing': [t.timing for t in med.timings] if med.timings else []
                                })
                            for report in prescription.test_reports:
                                prescription_data['test_reports'].append({
                                    'report_name': report.report_name, 'report_notes': report.report_notes,
                                    'price': float(report.price) if report.price is not None else 0.0,
                                    'status': report.status, 'file_path': report.file_path
                                })
                            prescriptions_data.append(prescription_data)

                        bot_response_text = "Here are your active prescriptions:"
                        # Format for chatbot display
                        if prescriptions_data:
                            for p_data in prescriptions_data:
                                bot_response_text += f"\n\n--- Prescription ID: {p_data['id']} ---"
                                bot_response_text += f"\nDate: {p_data['appointment_date']} with Dr. {p_data['doctor_name']}"
                                if p_data['medications']:
                                    bot_response_text += "\nMedications:"
                                    for med in p_data['medications']:
                                        bot_response_text += f"\n  - {med['name']} ({med['dosage']}, {med['meal_instructions']} {', '.join(med['timing'])})"
                                if p_data['test_reports']:
                                    bot_response_text += "\nTests:"
                                    for test in p_data['test_reports']:
                                        bot_response_text += f"\n  - {test['report_name']} (Status: {test['status']})"
                        else:
                            bot_response_text = f"No active prescriptions found."
            else:
                bot_response_text = "I cannot retrieve prescriptions without a linked patient profile."

            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu'

    elif current_state == 'medicine_select_prescription':
        selected_prescription = next(
            (p for p in updated_context.get('active_prescriptions', []) if p['id'] == user_selection_value), None)
        if selected_prescription:
            updated_context['current_medicine_request'] = {
                'patient_id': patient_id,
                'requester_user_id': user_obj.id,
                'delivery_address': patient_address or 'Unknown Address',
                'items': selected_prescription['items']
            }
            total_prescription_amount = sum(
                item['quantity_prescribed'] * item['unit_price'] for item in selected_prescription['items'])
            bot_response_text = f"Requesting all medicines from Prescription #{selected_prescription['id']}. Total estimated amount: Rs. {total_prescription_amount:.2f}."
            bot_options = [
                {"text": "Confirm Delivery", "value": "confirm_delivery"},
                {"text": "Modify Items", "value": "modify_items"},
                {"text": "Cancel", "value": "cancel_request"}
            ]  # These specific options might not be in config if they are very flow-specific.
            # But if they are reusable, put them in config!
            next_state = 'medicine_delivery_confirm'
        else:
            bot_response_text = "Invalid prescription selected. Please try again."
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu'


    # ... (Continue replacing hardcoded options with CHATBOT_CONFIG.get('some_key_options') ) ...

    elif current_state == 'medicine_quantity':
        if user_selection_value == 'other_quantity':
            bot_response_text = "Please type the exact quantity you need."
            next_state = 'medicine_other_quantity_input'
        elif user_selection_value:
            quantity = int(user_selection_value)
            if quantity > 0:
                updated_context['current_medicine_request']['items'][0]['quantity'] = quantity
                bot_response_text = f"You selected {quantity} units. Confirm delivery address: {updated_context['current_medicine_request']['delivery_address']}?"
                bot_options = get_chatbot_options('medicine_address_options')
                next_state = 'medicine_delivery_address'
            else:
                bot_response_text = "Invalid quantity. Please select an option or type a number."
                bot_options = get_chatbot_options('medicine_quantity_options')
                next_state = 'medicine_quantity'

    elif current_state == 'medicine_delivery_address':
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

    elif current_state == 'medicine_payment_method':
        if user_selection_value in [opt['value'] for opt in
                                    get_chatbot_options('medicine_payment_options')]:  # Validate against config
            updated_context['current_medicine_request']['payment_method'] = user_selection_value.replace('_', ' ')
            bot_response_text = f"Okay, payment method: {user_selection_value.replace('_', ' ')}. Ready to place your order?"
            bot_options = get_chatbot_options('medicine_final_confirm_options')
            next_state = 'medicine_final_confirm'
        else:
            bot_response_text = "Please select a payment method."
            bot_options = get_chatbot_options('medicine_payment_options')
            next_state = 'medicine_payment_method'


    elif current_state == 'ambulance_emergency_input':  # This state expects selection from buttons
        if user_selection_value == 'other_emergency':
            bot_response_text = "Please describe the emergency."
            next_state = 'ambulance_other_emergency_text_input'
        elif user_selection_value:
            # You might want to use the 'description' from your config here if it exists
            selected_emergency_text = next(
                (opt['text'] for opt in get_chatbot_options('ambulance_emergency_options') if
                 opt['value'] == user_selection_value), user_selection_value.replace('_', ' ').title())
            updated_context['current_ambulance_request']['emergency_description'] = selected_emergency_text
            bot_response_text = f"Ambulance request summary: Pickup at {updated_context['current_ambulance_request']['pickup_location']}. Emergency: {updated_context['current_ambulance_request']['emergency_description']}. Confirm dispatch?"
            bot_options = get_chatbot_options('ambulance_final_confirm_options')
            next_state = 'ambulance_final_confirm'
        else:
            bot_response_text = "Please select the nature of the emergency."
            bot_options = get_chatbot_options('ambulance_emergency_options')
            next_state = 'ambulance_emergency_input'

    # Fallback to main menu if 'menu' is typed
    if user_message and user_message.lower() == 'menu':
        bot_response_text = "Returning to main menu."
        next_state = 'main_menu'
        bot_options = get_chatbot_options('main_menu_options')

    # --- Return the response ---
    return jsonify({
        "message": bot_response_text,
        "options": bot_options,
        "next_state": next_state,
        "context": updated_context
    }), 200


@chatbot.route("/api/view-prescriptions", methods=['GET'], endpoint="view_patient_prescriptions")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def view_patient_prescriptions(current_user):
    try:
        # Get patient record
        patient = Patient.query.filter_by(user_id=current_user).first()
        if not patient:
            # If no patient record found for the user, return a 404 JSON error
            return jsonify({
                "message": "Patient profile not found for the current user.",
                "prescriptions": []
            }), 404

        appointments = Appointment.query.filter_by(patient_id=patient.id).all()
        appointment_ids = [appointment.id for appointment in appointments]

        if not appointment_ids:
            return jsonify({
                "message": f"No appointments found for {patient.first_name} {patient.last_name}.",
                "patient_name": f"{patient.first_name} {patient.last_name}",
                "prescriptions": []
            }), 200  # Return 200 with empty list if no appointments, not an error

        # Get all prescriptions for these appointments
        prescriptions = Prescription.query.filter(
            Prescription.appointment_id.in_(appointment_ids),
            Prescription.is_deleted == False
        ).all()

        if not prescriptions:
            return jsonify({
                "message": f"No active prescriptions found for {patient.first_name} {patient.last_name}.",
                "patient_name": f"{patient.first_name} {patient.last_name}",
                "prescriptions": []
            }), 200  # Return 200 with empty list if no prescriptions

        # Prepare the response data
        prescriptions_data = []
        for prescription in prescriptions:
            prescription_data = {
                'id': prescription.id,
                'appointment_id': prescription.appointment_id,
                # Ensure date is formatted to ISO 8601 string for JSON consistency
                'appointment_date': prescription.appointment.date.isoformat() if prescription.appointment and prescription.appointment.date else None,
                'doctor_name': f"{prescription.appointment.doctor.first_name} {prescription.appointment.doctor.last_name}" if prescription.appointment and prescription.appointment.doctor else None,
                'notes': prescription.notes,
                'status': prescription.status,
                'created_at': prescription.created_at.isoformat() if prescription.created_at else None,
                'medications': [],
                'test_reports': []
            }

            # Add medications
            for med in prescription.medications:
                medication = {
                    'name': med.name,
                    'dosage': med.dosage,
                    'meal_instructions': med.meal_instructions,
                    'timing': [t.timing for t in med.timings] if med.timings else []  # Ensure timings is iterable
                }
                prescription_data['medications'].append(medication)

            # Add test reports
            for report in prescription.test_reports:
                test_report = {
                    'report_name': report.report_name,
                    'report_notes': report.report_notes,
                    'price': float(report.price) if report.price is not None else 0.0,  # Ensure price is float
                    'status': report.status,
                    'file_path': report.file_path
                }
                prescription_data['test_reports'].append(test_report)

            prescriptions_data.append(prescription_data)

        # Return JSON response with the prescriptions data
        return jsonify({
            "message": "Prescriptions retrieved successfully.",
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "prescriptions": prescriptions_data
        }), 200

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error in view_patient_prescriptions API: {e}")
        return jsonify({
            "message": "An internal server error occurred while retrieving prescriptions.",
            "error": str(e)
        }), 500
