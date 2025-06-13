import traceback

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from controllers.chat_bot_controllers.utils.helper_funcation import get_chatbot_options
from models import Medicine, MedicineRequestStatus, UserRole, Prescription, Appointment, MedicineRequest, \
    MedicineRequestItem
from utils.config import db


# --- Medicine Request Flow ---
def get_cart_item_options(items):
    item_options = []
    if not items:
        return item_options

    for i, item in enumerate(items):
        item_options.append({
            "text": f"Modify/Remove {item['medicine_name']}",
            "value": f"modify_item_{item['medicine_id']}"
        })
    return item_options


def handle_medicine_request_start(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = []
    next_state = 'medicine_request_start'

    if 'current_medicine_request' not in chat_context or not chat_context['current_medicine_request'].get('items'):
        chat_context['current_medicine_request'] = {
            'patient_id': user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None,
            'requester_user_id': user_obj.id,
            'items': [],  # This will store items in the 'cart'
            'delivery_address': user_obj.patient.address if user_obj.role == UserRole.PATIENT and user_obj.patient else None,
            'payment_method': None,
            'status': MedicineRequestStatus.PENDING.value  # Initial status
        }
        # Add user's known address to context if available
        if user_obj.role == UserRole.PATIENT and user_obj.patient and user_obj.patient.address:
            chat_context['current_medicine_request']['delivery_address'] = user_obj.patient.address

    if user_selection_value == 'search_by_name':
        bot_response_text = "Please type the name or medicine number you are looking for."
        next_state = 'medicine_search_input'
        bot_options = []  # No buttons, expects text input

    elif user_selection_value == 'view_prescriptions':
        if user_obj.role == UserRole.PATIENT and user_obj.patient:
            patient_id = user_obj.patient.id
            appointments = Appointment.query.filter_by(patient_id=patient_id).all()
            appointment_ids = [appointment.id for appointment in appointments]

            if not appointment_ids:
                bot_response_text = "No appointments found to base prescriptions on."
                bot_options = get_chatbot_options('main_menu_options')
                next_state = 'main_menu_options'  # Go back to main menu
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
                            'appointment_date': prescription.appointment.date if prescription.appointment and prescription.appointment.date else None,
                            # Keep as string for simple comparison, or format for display
                            'doctor_name': f"{prescription.appointment.doctor.first_name} {prescription.appointment.doctor.last_name}" if prescription.appointment and prescription.appointment.doctor else None,
                            'notes': prescription.notes,
                            'status': prescription.status,
                            'medications': [
                                {'name': med.name, 'dosage': med.dosage, 'meal_instructions': med.meal_instructions,
                                 'timing': [t.timing for t in med.timings] if med.timings else [],
                                 'medicine_id': med.id,  # Crucial: store medicine ID
                                 'current_stock': med.current_stock,
                                 'default_mrp': float(med.default_mrp) if med.default_mrp else 0.0
                                 } for med in prescription.medications]
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
                                if med['current_stock'] <= 0:
                                    bot_response_text += " (Out of Stock)"
                                else:
                                    bot_response_text += f" (In Stock: {med['current_stock']})"
                        else:
                            bot_response_text += "\n  No medications listed."

                    chat_context['active_prescriptions'] = prescriptions_data
                    bot_options = [{"text": f"Select Prescription {p['id']}", "value": str(p['id'])} for p in
                                   prescriptions_data]
                    next_state = 'medicine_select_prescription'
                else:
                    bot_response_text = "No active prescriptions found."
                    bot_options = get_chatbot_options('main_menu_options')
                    next_state = 'main_menu_options'
        else:
            bot_response_text = "I cannot retrieve prescriptions without a linked patient profile."
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu_options'
    elif user_selection_value == 'view_cart':
        return view_medicine_cart(user_obj, data, chat_context)
    elif user_selection_value == 'check_status':
        return handle_medicine_check_status(user_obj, data, chat_context)
    else:
        bot_response_text = "How would you like to request medicine?"
        bot_options = get_chatbot_options('medicine_request_options')
        next_state = 'medicine_request_start'

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_select_prescription(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = []
    next_state = 'medicine_select_prescription'

    selected_prescription = next(
        (p for p in chat_context.get('active_prescriptions', []) if str(p['id']) == user_selection_value), None)

    if selected_prescription:
        chat_context['selected_prescription_id'] = selected_prescription['id']  # Store for later reference
        bot_response_text = f"You selected Prescription #{selected_prescription['id']}. Here are the medications:"

        # Present each medication with an "Add to Cart" option
        for med in selected_prescription.get('medications', []):
            stock_info = f" (In Stock: {med['current_stock']})" if med['current_stock'] > 0 else " (Out of Stock)"
            bot_response_text += f"\n- {med['name']} ({med['dosage']}){stock_info}"
            if med['current_stock'] > 0:
                bot_options.append({
                    "text": f"Add {med['name']} to Cart",
                    "value": f"add_med_{med['medicine_id']}"
                })

        bot_response_text += "\n\nWhat would you like to do?"
        bot_options.extend([
            {"text": "Go to Cart", "value": "view_cart"},
            {"text": "Search for another medicine", "value": "search_by_name"},
            {"text": "Back to Main Menu", "value": "main_menu"}
        ])
        next_state = 'medicine_item_selection'
    else:
        bot_response_text = "Invalid prescription selected. Please try again or go back to the main menu."
        bot_options = get_chatbot_options('main_menu_options')  # Provide main menu options
        next_state = 'main_menu_options'

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_item_selection(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = []
    next_state = 'medicine_item_selection'  # Default to staying in this state

    current_medicine_request = chat_context.setdefault('current_medicine_request', {
        'items': [], 'status': MedicineRequestStatus.PENDING.value
    })

    if user_selection_value and user_selection_value.startswith('add_med_'):
        medicine_id = int(user_selection_value.replace('add_med_', ''))
        # print(f"Attempting to add medicine with ID: {medicine_id}")
        medicine = Medicine.query.get(medicine_id)
        # print(f"Medicine object found: {medicine.name if medicine else 'None'}")

        if medicine and medicine.current_stock > 0:
            found_in_cart = False
            for item in current_medicine_request['items']:
                if item['medicine_id'] == medicine.id:
                    # Check if increasing quantity would exceed stock
                    if item['quantity_requested'] + 1 > medicine.current_stock:
                        bot_response_text = f"Cannot add more {medicine.name}. Only {medicine.current_stock} units are in stock."
                    else:
                        item['quantity_requested'] += 1
                        bot_response_text = f"Added another unit of {medicine.name} to your cart. Current quantity: {item['quantity_requested']}. "
                    found_in_cart = True
                    break

            if not found_in_cart:
                current_medicine_request['items'].append({
                    'medicine_id': medicine.id,
                    'medicine_name': medicine.name,
                    'quantity_requested': 1,
                    'unit_price': float(medicine.default_mrp) if medicine.default_mrp else 0.0,
                    'stock_available': medicine.current_stock  # Store current stock for local checks
                })
                bot_response_text = f"Added {medicine.name} to your cart. "

            bot_response_text += "What else would you like to do?"
            bot_options = get_chatbot_options('medicine_cart_options')

            next_state = 'medicine_item_selection'  # Stay here for more additions or cart actions

        elif medicine and medicine.current_stock <= 0:
            bot_response_text = f"Sorry, {medicine.name} is currently out of stock."
            bot_options = get_chatbot_options('medicine_cart_options')

        else:
            bot_response_text = "Invalid medicine selected or not found."
            bot_options = get_chatbot_options('medicine_cart_options')

    elif user_selection_value == 'view_cart':
        return view_medicine_cart(user_obj, data, chat_context)

    elif user_selection_value == 'checkout':
        if not current_medicine_request['items']:
            bot_response_text = "Your cart is empty. Please add medicines before checking out."
            bot_options = get_chatbot_options('medicine_request_options')  # Back to start options
            next_state = 'medicine_request_start'
        else:
            return handle_medicine_delivery_address(user_obj, data, chat_context)

    elif user_selection_value == 'cancel_order':
        chat_context['current_medicine_request'] = {
            'items': [], 'status': MedicineRequestStatus.CANCELLED.value
        }
        bot_response_text = "Your current medicine order has been cancelled."
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'

    elif user_selection_value == 'search_by_name':
        bot_response_text = "Please type the name or medicine number you are looking for."
        next_state = 'medicine_search_input'
        bot_options = []

    elif user_selection_value == 'view_prescriptions':
        return handle_medicine_request_start(user_obj, {'selection_value': 'view_prescriptions'}, chat_context)

    elif user_selection_value == 'main_menu':
        bot_response_text = "Returning to main menu."
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'

    elif user_selection_value == 'clear_cart':  # NEW
        chat_context['current_medicine_request']['items'] = []
        bot_response_text = "Your cart has been cleared. What would you like to do now?"
        bot_options = get_chatbot_options('medicine_request_options')  # Back to start options
        next_state = 'medicine_request_start'

    elif user_selection_value.startswith('modify_item_'):  # NEW: User wants to modify a specific item
        medicine_id = int(user_selection_value.replace('modify_item_', ''))
        chat_context['modifying_medicine_id'] = medicine_id
        return handle_medicine_modify_item(user_obj, data, chat_context)

    # NEW: Handling increase/decrease/remove from handle_medicine_modify_item
    elif user_selection_value == 'increase_item_qty':
        medicine_id = chat_context.get('modifying_medicine_id')
        if medicine_id:
            return adjust_medicine_quantity(user_obj, chat_context, medicine_id, 1)
        else:
            bot_response_text = "I'm not sure which item to increase. Please select it from the cart again."
            return view_medicine_cart(user_obj, data, chat_context)

    elif user_selection_value == 'decrease_item_qty':
        medicine_id = chat_context.get('modifying_medicine_id')
        if medicine_id:
            return adjust_medicine_quantity(user_obj, chat_context, medicine_id, -1)
        else:
            bot_response_text = "I'm not sure which item to decrease. Please select it from the cart again."
            return view_medicine_cart(user_obj, data, chat_context)

    elif user_selection_value == 'remove_specific_item':  # NEW
        medicine_id = chat_context.get('modifying_medicine_id')
        if medicine_id:
            return remove_medicine_from_cart(user_obj, chat_context, medicine_id)
        else:
            bot_response_text = "I'm not sure which item to remove. Please select it from the cart again."
            return view_medicine_cart(user_obj, data, chat_context)

    elif user_selection_value == 'set_specific_qty':  # NEW: Route to quantity input
        medicine_id = chat_context.get('modifying_medicine_id')
        if medicine_id:
            # Set context for handle_medicine_quantity_input
            chat_context['setting_quantity_for_medicine_id'] = medicine_id
            found_item = next(
                (item for item in current_medicine_request['items'] if item['medicine_id'] == medicine_id), None)
            medicine_db_obj = Medicine.query.get(medicine_id)  # Fetch latest stock
            stock_info = f" (Current stock: {medicine_db_obj.current_stock})" if medicine_db_obj else ""
            bot_response_text = f"Please enter the new quantity for {found_item['medicine_name'] if found_item else 'this medicine'}{stock_info}:"
            bot_options = []  # Expect text input
            next_state = 'medicine_quantity_input'
        else:
            bot_response_text = "I'm not sure which item's quantity to set. Please select it from the cart again."
            return view_medicine_cart(user_obj, data, chat_context)

    elif user_selection_value == 'medicine_request_start':  # For button "Back to Medicine Request Start"
        return handle_medicine_request_start(user_obj, data, chat_context)

    else:
        bot_response_text = "What would you like to do next?"
        bot_options = get_chatbot_options('medicine_cart_options')

    return bot_response_text, bot_options, next_state, chat_context


def view_medicine_cart(user_obj, data, chat_context):
    current_medicine_request = chat_context.get('current_medicine_request', {'items': []})
    items = current_medicine_request.get('items', [])
    bot_options = get_chatbot_options('medicine_cart_options')  # Always offer general cart options

    if not items:
        bot_response_text = "Your cart is empty. Add some medicines first!"
        next_state = 'medicine_request_start'  # Redirect to add options
        bot_options = get_chatbot_options('medicine_request_options')
    else:
        total_amount = sum(item['quantity_requested'] * item['unit_price'] for item in items)
        bot_response_text = "Here's what's in your cart:\n"
        for i, item in enumerate(items):
            bot_response_text += f"\n{i + 1}. {item['medicine_name']} - Quantity: {item['quantity_requested']} (Rs. {item['unit_price']:.2f} each)"
            if item['quantity_requested'] > item[
                'stock_available']:  # Highlight if quantity exceeds available stock (shouldn't happen with proper flow)
                bot_response_text += " (Quantity exceeds stock!)"

        bot_response_text += f"\n\nTotal Estimated Amount: Rs. {total_amount:.2f}"
        bot_response_text += "\n\nWhat would you like to do?"
        next_state = 'medicine_item_selection'  # Stay in item selection state

        item_specific_options = get_cart_item_options(items)
        bot_options = item_specific_options + bot_options  # Add item-specific options first

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_set_item_quantity(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = []
    next_state = 'medicine_item_selection'

    current_medicine_request = chat_context.get('current_medicine_request', {'items': []})

    if user_selection_value and user_selection_value.startswith('set_qty_'):
        medicine_id = int(user_selection_value.replace('set_qty_', ''))
        found_item = next((item for item in current_medicine_request['items'] if item['medicine_id'] == medicine_id),
                          None)

        if found_item:
            chat_context['setting_quantity_for_medicine_id'] = medicine_id  # Store for next input
            medicine_db_obj = Medicine.query.get(medicine_id)  # Fetch latest stock
            stock_info = f" (Current stock: {medicine_db_obj.current_stock})" if medicine_db_obj else ""
            bot_response_text = f"How many units of {found_item['medicine_name']} do you need?{stock_info}"
            bot_options = []  # Expects text input
            next_state = 'medicine_quantity_input'
        else:
            bot_response_text = "That medicine is not in your cart or is invalid. Please select an item from your cart to modify quantity."
            bot_options = get_chatbot_options('medicine_cart_options')
            next_state = 'medicine_item_selection'
    else:
        bot_response_text = "Please select a medicine from your cart to modify its quantity."
        bot_options = get_chatbot_options('medicine_cart_options')
        next_state = 'medicine_item_selection'

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_quantity_input(user_obj, data, chat_context):
    user_message = data.get('message')
    bot_response_text = ""
    bot_options = []
    next_state = 'medicine_item_selection'

    current_medicine_request = chat_context.setdefault('current_medicine_request', {
        'items': [], 'status': MedicineRequestStatus.PENDING.value
    })

    medicine_id_to_set_qty = chat_context.get('setting_quantity_for_medicine_id')

    if medicine_id_to_set_qty is None:
        bot_response_text = "It seems I lost track of which medicine you wanted to set the quantity for. Please try again from the cart."
        bot_options = get_chatbot_options('medicine_cart_options')
        next_state = 'medicine_item_selection'
        return bot_response_text, bot_options, next_state, chat_context

    try:
        new_quantity = int(user_message)
        if new_quantity <= 0:
            raise ValueError("Quantity must be a positive number.")
    except (ValueError, TypeError):
        bot_response_text = "Invalid quantity. Please enter a valid positive number (e.g., 1, 5, 10)."
        bot_options = []
        next_state = 'medicine_quantity_input'
        return bot_response_text, bot_options, next_state, chat_context

    item_in_cart = next(
        (item for item in current_medicine_request['items'] if item['medicine_id'] == medicine_id_to_set_qty), None)
    medicine_db_obj = Medicine.query.get(medicine_id_to_set_qty)

    if not item_in_cart or not medicine_db_obj:
        bot_response_text = "The medicine you tried to set the quantity for is no longer in your cart or found. Please try again from the cart."
        bot_options = get_chatbot_options('medicine_cart_options')
        next_state = 'medicine_item_selection'
        chat_context.pop('setting_quantity_for_medicine_id', None)
        return bot_response_text, bot_options, next_state, chat_context

    available_stock = medicine_db_obj.current_stock

    if new_quantity > available_stock:
        bot_response_text = f"Sorry, only {available_stock} units of {item_in_cart['medicine_name']} are currently in stock. Please enter a quantity within stock."
        bot_options = []
        next_state = 'medicine_quantity_input'
        return bot_response_text, bot_options, next_state, chat_context

    item_in_cart['quantity_requested'] = new_quantity
    item_in_cart['stock_available'] = available_stock

    bot_response_text = f"Quantity for {item_in_cart['medicine_name']} has been updated to {new_quantity}. What else would you like to do?"
    bot_options = get_chatbot_options('medicine_cart_options')
    next_state = 'medicine_item_selection'
    chat_context.pop('setting_quantity_for_medicine_id', None)

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_delivery_address(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    message_text = data.get('message')  # Used if user types new address (though handled by medicine_new_address_input)

    current_medicine_request = chat_context.get('current_medicine_request', {})
    # Ensure current_medicine_request is properly initialized or re-initialized with user data
    if not current_medicine_request.get('patient_id'):
        current_medicine_request[
            'patient_id'] = user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None
        current_medicine_request['requester_user_id'] = user_obj.id

    bot_response_text = "Great! Let's proceed to checkout. First, please confirm your delivery address."
    bot_options = get_chatbot_options('medicine_address_options')
    next_state = 'medicine_delivery_address'  # Default to staying here

    patient_address = user_obj.patient.address if user_obj.role == UserRole.PATIENT and user_obj.patient else None
    current_delivery_address_in_context = current_medicine_request.get('delivery_address')

    if not user_selection_value and not message_text:
        if current_delivery_address_in_context:
            # If an address is already in context (e.g., from profile or previous input in this session)
            bot_response_text = f"The delivery address is currently set to: '{current_delivery_address_in_context}'. Is this correct?"
            bot_options = get_chatbot_options('medicine_address_options')
            next_state = 'medicine_delivery_address'
        elif patient_address:
            # If no address in context but patient has one, suggest it.
            current_medicine_request['delivery_address'] = patient_address  # Pre-fill from profile
            bot_response_text = f"The delivery address is currently set to: '{patient_address}'. Is this correct?"
            bot_options = get_chatbot_options('medicine_address_options')
            next_state = 'medicine_delivery_address'
        else:
            # No address in profile or context, directly ask for new input.
            bot_response_text = "Please provide the full delivery address."
            next_state = 'medicine_new_address_input'
            bot_options = []  # Expecting text input

    elif user_selection_value == 'confirm_address':
        if current_delivery_address_in_context:  # Only confirm if an address is actually present
            bot_response_text = "How would you like to pay for your order?"
            bot_options = get_chatbot_options('medicine_payment_options')
            next_state = 'medicine_payment_method'
        else:
            bot_response_text = "No address is set to confirm. Please provide the full delivery address."
            next_state = 'medicine_new_address_input'
            bot_options = []

    elif user_selection_value == 'enter_new_address':
        bot_response_text = "Please type the new delivery address."
        next_state = 'medicine_new_address_input'
        bot_options = []  # Expecting text input

    # Store updated address back to context
    chat_context['current_medicine_request'] = current_medicine_request
    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_new_address_input(user_obj, data, chat_context):
    message_text = data.get('message')
    bot_response_text = ""
    bot_options = []
    next_state = 'medicine_verify_new_address'  # Next state is to process the input

    current_medicine_request = chat_context.get('current_medicine_request', {})

    if message_text and message_text.strip():
        current_medicine_request['delivery_address'] = message_text.strip()
        bot_response_text = f"You entered: '{message_text.strip()}'. Is this correct?"
        bot_options = get_chatbot_options('medicine_verify_address_options')
        chat_context['current_medicine_request'] = current_medicine_request  # Update context
    else:
        bot_response_text = "Please type the new delivery address."
        next_state = 'medicine_new_address_input'  # Stay in this state
        bot_options = []  # Expecting text input

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_verify_new_address(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    current_medicine_request = chat_context.get('current_medicine_request', {})
    bot_response_text = ""
    bot_options = []
    next_state = 'medicine_verify_new_address'  # Default

    if user_selection_value == 'address_correct':
        bot_response_text = f"Address confirmed as '{current_medicine_request.get('delivery_address', 'N/A')}'. How would you like to pay?"
        bot_options = get_chatbot_options('medicine_payment_options')
        next_state = 'medicine_payment_method'
    elif user_selection_value == 'address_re_enter':
        bot_response_text = "Okay, please type the new delivery address again."
        next_state = 'medicine_new_address_input'
        bot_options = []  # Expecting text input
    else:
        bot_response_text = "Please confirm the address or choose to re-enter it."
        bot_options = get_chatbot_options('medicine_verify_address_options')
        next_state = 'medicine_verify_new_address'

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_payment_method(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    current_medicine_request = chat_context.get('current_medicine_request', {})
    bot_response_text = ""
    bot_options = []
    next_state = 'medicine_payment_method'  # Default

    # Ensure current_medicine_request has items for calculation
    if not current_medicine_request.get('items'):
        bot_response_text = "Your cart is empty. Please add medicines before proceeding with payment."
        bot_options = get_chatbot_options('medicine_request_options')
        next_state = 'medicine_request_start'
        return bot_response_text, bot_options, next_state, chat_context

    if user_selection_value in [opt['value'] for opt in get_chatbot_options('medicine_payment_options')]:
        current_medicine_request['payment_method'] = user_selection_value.replace('_', ' ')

        # Calculate total amount for display
        total_amount = sum(
            item['quantity_requested'] * item['unit_price'] for item in current_medicine_request.get('items', []))

        bot_response_text = f"Payment method selected: {user_selection_value.replace('_', ' ')}. Your order total is Rs. {total_amount:.2f}. Ready to place your order?"
        bot_options = get_chatbot_options('medicine_final_confirm_options')
        next_state = 'medicine_final_confirm'
    else:
        bot_response_text = "Please select a valid payment method."
        bot_options = get_chatbot_options('medicine_payment_options')
        next_state = 'medicine_payment_method'

    chat_context['current_medicine_request'] = current_medicine_request
    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_final_confirm(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    current_medicine_request = chat_context.get('current_medicine_request', {})
    bot_response_text = ""
    bot_options = []
    next_state = 'main_menu_options'  # Default after completion/cancellation

    if user_selection_value == 'place_order':
        if not current_medicine_request.get('items'):
            bot_response_text = "Your cart is empty. Cannot place an empty order."
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu_options'
            return bot_response_text, bot_options, next_state, chat_context

        try:
            # Create the MedicineRequest entry
            new_request = MedicineRequest(
                patient_id=current_medicine_request.get('patient_id'),
                requester_user_id=current_medicine_request.get('requester_user_id'),
                delivery_address=current_medicine_request.get('delivery_address'),
                payment_method=current_medicine_request.get('payment_method'),
                status=MedicineRequestStatus.PENDING.value  # Ensure status is set
            )
            db.session.add(new_request)
            db.session.flush()  # Flush to get the ID before adding items

            total_order_amount = 0.0
            # Add MedicineRequestItem entries
            for item_data in current_medicine_request['items']:
                medicine = Medicine.query.get(item_data['medicine_id'])
                if not medicine or medicine.current_stock < item_data['quantity_requested']:
                    db.session.rollback()  # Rollback the request if stock issues
                    bot_response_text = f"Order failed: Insufficient stock for {item_data['medicine_name']} (only {medicine.current_stock if medicine else 0} available). Please adjust your cart."
                    next_state = 'medicine_item_selection'
                    bot_options = get_chatbot_options('medicine_cart_options')
                    return bot_response_text, bot_options, next_state, chat_context

                new_request_item = MedicineRequestItem(
                    medicine_request_id=new_request.id,
                    medicine_id=item_data['medicine_id'],
                    quantity=item_data['quantity_requested'],
                    requested_price_per_unit=item_data['unit_price'],
                    subtotal=item_data['quantity_requested'] * item_data['unit_price']
                )
                db.session.add(new_request_item)
                total_order_amount += new_request_item.subtotal

                # Deduct stock immediately
                # medicine.current_stock -= item_data['quantity_requested']
                db.session.add(medicine)  # Persist stock change

            new_request.total_amount = total_order_amount  # Update total amount on the request
            db.session.commit()

            bot_response_text = f"Your medicine order (ID: {new_request.id}) has been placed successfully! Total amount: Rs. {total_order_amount:.2f}. We will notify you when it's dispatched."
            # Clear current request from context
            chat_context['current_medicine_request'] = {'items': [], 'status': MedicineRequestStatus.CONFIRMED.value}
            chat_context.pop('selected_prescription_id', None)
            chat_context.pop('search_results', None)
            chat_context.pop('medicine_id_for_quantity_input', None)
            chat_context.pop('modifying_medicine_id', None)  # Clear this too
            chat_context.pop('setting_quantity_for_medicine_id', None)  # Clear this too

            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu_options'

        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            print(f"Error placing medicine order: {e}")
            bot_response_text = "There was an error placing your order. Please try again later or contact support."
            bot_options = get_chatbot_options('main_menu_options')
            next_state = 'main_menu_options'

    elif user_selection_value == 'go_back':
        bot_response_text = "Returning to payment method selection."
        bot_options = get_chatbot_options('medicine_payment_options')
        next_state = 'medicine_payment_method'
    else:
        bot_response_text = "Please confirm your order or choose to go back."
        bot_options = get_chatbot_options('medicine_final_confirm_options')
        next_state = 'medicine_final_confirm'

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_modify_item(user_obj, data, chat_context):
    medicine_id = chat_context.get('modifying_medicine_id')
    current_medicine_request = chat_context.get('current_medicine_request', {'items': []})
    bot_options = get_chatbot_options('medicine_modify_item_options')
    next_state = 'medicine_item_selection'

    if not medicine_id:
        bot_response_text = "I'm not sure which medicine you want to modify. Please select it from your cart."
        return view_medicine_cart(user_obj, data, chat_context)

    item_in_cart = next(
        (item for item in current_medicine_request['items'] if item['medicine_id'] == medicine_id), None)

    if not item_in_cart:
        bot_response_text = "That medicine is no longer in your cart. Please select another item or go back."
        return view_medicine_cart(user_obj, data, chat_context)

    bot_response_text = f"You are modifying '{item_in_cart['medicine_name']}'. Current quantity: {item_in_cart['quantity_requested']}. What would you like to do?"

    return bot_response_text, bot_options, next_state, chat_context


def adjust_medicine_quantity(user_obj, chat_context, medicine_id, change_amount):
    current_medicine_request = chat_context.get('current_medicine_request', {'items': []})
    item_in_cart = next(
        (item for item in current_medicine_request['items'] if item['medicine_id'] == medicine_id), None)

    bot_response_text = ""
    next_state = 'medicine_item_selection'  # Always return to cart view or item selection
    bot_options = get_chatbot_options('medicine_cart_options')
    bot_options.extend(get_cart_item_options(current_medicine_request['items']))  # Show item specific options too

    if not item_in_cart:
        bot_response_text = "The medicine is not in your cart."
        return bot_response_text, bot_options, next_state, chat_context

    medicine_db_obj = Medicine.query.get(medicine_id)
    if not medicine_db_obj:
        bot_response_text = "Medicine details not found in our system. Cannot adjust quantity."
        return bot_response_text, bot_options, next_state, chat_context

    new_quantity = item_in_cart['quantity_requested'] + change_amount

    if new_quantity <= 0:
        return remove_medicine_from_cart(user_obj, chat_context,
                                         medicine_id)  # If quantity goes to 0 or less, remove it
    elif new_quantity > medicine_db_obj.current_stock:
        bot_response_text = f"Cannot increase quantity. Only {medicine_db_obj.current_stock} units of {item_in_cart['medicine_name']} are in stock."
    else:
        item_in_cart['quantity_requested'] = new_quantity
        bot_response_text = f"Quantity for {item_in_cart['medicine_name']} updated to {new_quantity}. Your cart is now:"

    return view_medicine_cart(user_obj, {}, chat_context)


def remove_medicine_from_cart(user_obj, chat_context, medicine_id_to_remove):
    current_medicine_request = chat_context.get('current_medicine_request', {'items': []})
    initial_item_count = len(current_medicine_request['items'])

    current_medicine_request['items'] = [
        item for item in current_medicine_request['items'] if item['medicine_id'] != medicine_id_to_remove
    ]

    bot_response_text = ""
    next_state = 'medicine_item_selection'
    bot_options = get_chatbot_options('medicine_cart_options')
    bot_options.extend(get_cart_item_options(current_medicine_request['items']))

    if len(current_medicine_request['items']) < initial_item_count:
        bot_response_text = "Item removed from your cart. Your cart is now:"
    else:
        bot_response_text = "Could not find that item in your cart. Your cart is currently:"

    # Clear modifying context after action
    chat_context.pop('modifying_medicine_id', None)

    # After removal, always show the updated cart
    return view_medicine_cart(user_obj, {}, chat_context)


def handle_medicine_check_status(user_obj, data, chat_context):
    bot_response_text = ""
    bot_options = get_chatbot_options('medicine_order_status_options')  # Options after checking status
    next_state = 'medicine_request_start'  # Default back to main medicine options

    if user_obj.role != UserRole.PATIENT or not user_obj.patient:
        bot_response_text = "I can only check order status for linked patient profiles."
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'
        return bot_response_text, bot_options, next_state, chat_context

    patient_id = user_obj.patient.id

    last_request = MedicineRequest.query.filter_by(
        patient_id=patient_id
    ).order_by(
        MedicineRequest.request_date.desc()
    ).first()

    if not last_request:
        bot_response_text = "You don't have any past medicine requests."
    else:
        items_details = []

        request_items = MedicineRequestItem.query.filter_by(medicine_request_id=last_request.id).all()
        if request_items:
            for item in request_items:
                medicine = Medicine.query.get(item.medicine_id)  # Fetch medicine details
                items_details.append(f"- {medicine.name if medicine else 'Unknown Medicine'} (Qty: {item.quantity})")
        else:
            items_details = ["- No items found for this order (data might be incomplete)."]

        bot_response_text = (
                f"Your Last Order (ID: {last_request.id}):\n"
                f"Status: {last_request.status.value.upper()}\n"
                f"Delivery Address: {last_request.delivery_address}\n"
                f"Payment Method: {last_request.payment_method}\n"
                f"Total Amount: Rs. {last_request.total_amount:.2f}\n"
                f"Items:\n" + "\n".join(items_details)
        )
        if last_request.status == MedicineRequestStatus.PENDING.value:
            bot_response_text += "\n\nWe're processing your order. You can cancel it if needed."
            bot_options.append({"text": "Cancel This Order", "value": f"cancel_specific_order_{last_request.id}"})
        elif last_request.status == MedicineRequestStatus.CONFIRMED.value:
            bot_response_text += "\n\nYour order has been confirmed and is being prepared for dispatch."
        elif last_request.status == MedicineRequestStatus.DELIVERED.value:
            bot_response_text += "\n\nYour order has been delivered."
        elif last_request.status == MedicineRequestStatus.CANCELLED.value:
            bot_response_text += "\n\nThis order has been cancelled."

    bot_response_text += "\n\nWhat would you like to do next?"
    next_state = 'medicine_request_start'

    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_cancel_specific_order(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = get_chatbot_options('main_menu_options')
    next_state = 'main_menu_options'

    if not user_selection_value or not user_selection_value.startswith('cancel_specific_order_'):
        bot_response_text = "Invalid request to cancel order. Please try again from 'Check Status'."
        return handle_medicine_check_status(user_obj, data, chat_context)

    order_id = int(user_selection_value.replace('cancel_specific_order_', ''))
    patient_id = user_obj.patient.id if user_obj.role == UserRole.PATIENT and user_obj.patient else None

    if not patient_id:
        bot_response_text = "Cannot cancel order: no patient profile linked."
        return bot_response_text, bot_options, next_state, chat_context

    # Retrieve the order to cancel
    order_to_cancel = MedicineRequest.query.filter_by(id=order_id, patient_id=patient_id).first()

    if not order_to_cancel:
        bot_response_text = f"Order with ID {order_id} not found or you don't have permission to cancel it."
    elif order_to_cancel.status == MedicineRequestStatus.CANCELLED.value:
        bot_response_text = f"Order {order_id} is already cancelled."
    elif order_to_cancel.status == MedicineRequestStatus.DELIVERED.value:
        bot_response_text = f"Order {order_id} has already been delivered and cannot be cancelled."
    else:
        try:
            order_to_cancel.status = MedicineRequestStatus.CANCELLED.value
            db.session.add(order_to_cancel)
            db.session.commit()
            bot_response_text = f"Order {order_id} has been successfully cancelled."
        except Exception as e:
            db.session.rollback()
            print(f"Error cancelling order {order_id}: {e}")
            bot_response_text = f"There was an error cancelling order {order_id}. Please try again later."

    bot_options = get_chatbot_options('main_menu_options')  # After cancelling, go back to main menu
    next_state = 'main_menu_options'
    return bot_response_text, bot_options, next_state, chat_context


def handle_medicine_search_input(user_obj, data, chat_context):
    search_term = data.get('message')
    bot_options = []
    next_state = 'medicine_item_selection'  # Next state for selecting search results or cart actions

    if not search_term:
        bot_response_text = "Please enter a valid medicine name or number to search."
        bot_options = []  # Expects text input
        next_state = 'medicine_search_input'  # Stay in search input
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
    ).limit(5).all()  # Limit results to avoid overwhelming the user

    if not medicines:
        bot_response_text = f"No medicines found matching '{search_term}'. Would you like to try searching again or go back to the main menu?"
        bot_options = get_chatbot_options("medicine_not_found")
        next_state = 'medicine_request_start'  # Can go back to start of flow
    else:
        bot_response_text = f"Found the following medicines matching '{search_term}':"
        for med in medicines:
            stock_info = f" (In Stock: {med.current_stock})" if med.current_stock > 0 else " (Out of Stock)"
            bot_response_text += f"\n\n- {med.name} (#{med.medicine_number})"
            bot_response_text += f"\n  Category: {med.category.name if med.category else 'N/A'}"
            bot_response_text += f"\n  Price: ₹{float(med.default_mrp) if med.default_mrp else 'N/A'}"
            bot_response_text += stock_info

            if med.current_stock > 0:
                bot_options.append({
                    "text": f"Add {med.name} to Cart",
                    "value": f"add_med_{med.id}"
                })

        bot_response_text += "\n\nWhat would you like to do next?"
        bot_options.extend(get_chatbot_options('medicine_cart_options'))
        next_state = 'medicine_item_selection'

        # Store essential search results data in context to avoid re-querying
        chat_context['search_results'] = [{
            'id': med.id,
            'name': med.name,
            'current_stock': med.current_stock,
            'default_mrp': float(med.default_mrp) if med.default_mrp else 0.0
        } for med in medicines]

    return bot_response_text, bot_options, next_state, chat_context
