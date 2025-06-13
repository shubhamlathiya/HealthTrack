from controllers.chat_bot_controllers.utils.helper_funcation import get_chatbot_options
from models import db, Patient  # Assuming Patient is imported from your models


def handle_my_health_profile(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = []
    next_state = 'my_health_profile'

    if not user_obj:
        bot_response_text = "You're not logged in. Please log in to view or update your health profile."
        bot_options = get_chatbot_options('main_menu_options')
        return bot_response_text, bot_options, 'main_menu_options', chat_context

    patient = Patient.query.filter_by(user_id=user_obj.id, is_deleted=False).first()
    if not patient:
        bot_response_text = "No health profile found. Please contact admin or register as a patient."
        bot_options = get_chatbot_options('main_menu_options')
        return bot_response_text, bot_options, 'main_menu_options', chat_context

    if user_selection_value == 'my_health_profile':
        bot_response_text = (
            "👤 Welcome to your Health Profile! What would you like to do?\n\n"
            "• 📄 **View Profile** – See your saved personal and health details.\n"
            "• 📞 **Update Contact Info** – Edit your phone number or email.\n"
            "• 🩺 **Update Health Info** – Add or modify health-related data."
        )

        bot_options = get_chatbot_options('profile_options')

    elif user_selection_value == 'profile_view':
        bot_response_text = (
            f"📄 **Your Profile Info**:\n\n"
            f"👤 Name: {patient.first_name} {patient.last_name}\n"
            f"📞 Phone: {patient.phone or 'N/A'}\n"
            f"🏠 Address: {patient.address or 'N/A'}\n"
            f"🎂 Age: {patient.age or 'N/A'}\n"
            f"⚧️ Gender: {patient.gender or 'N/A'}"
        )
        bot_options = get_chatbot_options('profile_options')

    elif user_selection_value == 'profile_update_contact':
        bot_response_text = "What would you like to update in contact info? (e.g., phone number, address)"
        next_state = 'profile_update_contact_input'

    elif user_selection_value == 'profile_update_health':
        bot_response_text = "What health info would you like to update? (e.g., age, gender)"
        next_state = 'profile_update_health_input'

    elif user_selection_value == 'main_menu':
        bot_response_text = "Returning to the main menu. How can I help you further?"
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'

    else:
        bot_response_text = "Invalid option. Please choose from the menu."
        bot_options = get_chatbot_options('profile_options')

    return bot_response_text, bot_options, next_state, chat_context


def handle_profile_update_contact_input(user_obj, data, chat_context):
    user_message = data.get('message', '').strip().lower()
    bot_response_text = ""
    bot_options = []
    next_state = 'profile_update_contact_input'

    patient = Patient.query.filter_by(user_id=user_obj.id, is_deleted=False).first()

    if not patient:
        return "Patient profile not found. Please try again later.", get_chatbot_options(
            'main_menu_options'), 'main_menu_options', chat_context

    # Step 1: Ask what to update (phone/address)
    if 'contact_update_field' not in chat_context:
        if 'phone' in user_message:
            chat_context['contact_update_field'] = 'phone'
            bot_response_text = "Please enter your new phone number:"
        elif 'address' in user_message:
            chat_context['contact_update_field'] = 'address'
            bot_response_text = "Please enter your new address:"
        else:
            bot_response_text = (
                "📇 What would you like to update?\n\n"
                "• To update your **phone number**, type **phone**.\n"
                "• To update your **address**, type **address**.\n\n"
                "You can also type **back** to return to the previous menu."
            )
            bot_options = []
    else:
        # Step 2: User provides new value
        update_field = chat_context['contact_update_field']

        if update_field == 'phone':
            import re
            number = ''.join(re.findall(r'\d+', user_message))
            if number:
                patient.phone = number
                db.session.commit()
                bot_response_text = f"📞 Phone number updated to: {number}"
            else:
                bot_response_text = "Invalid phone number. Please enter digits only."
                return bot_response_text, [], next_state, chat_context
        elif update_field == 'address':
            patient.address = user_message
            db.session.commit()
            bot_response_text = f"🏠 Address updated to: {user_message}"

        # Clear context and return to profile options
        chat_context.pop('contact_update_field', None)
        bot_options = get_chatbot_options('profile_options')
        next_state = 'my_health_profile'

    return bot_response_text, bot_options, next_state, chat_context


def handle_profile_update_health_input(user_obj, data, chat_context):
    user_message = data.get('message')
    bot_response_text = ""
    bot_options = []
    next_state = 'my_health_profile'

    patient = Patient.query.filter_by(user_id=user_obj.id, is_deleted=False).first()

    if patient and user_message:
        message = user_message.lower()
        if 'age' in message:
            import re
            age = ''.join(re.findall(r'\d+', message))
            if age.isdigit():
                patient.age = int(age)
                db.session.commit()
                bot_response_text = f"🎂 Age updated to: {age}"
            else:
                bot_response_text = "Invalid age format. Please try again."
                next_state = 'profile_update_health_input'
        elif 'gender' in message:
            gender = message.replace('gender', '').strip().capitalize()
            if gender in ['Male', 'Female', 'Other']:
                patient.gender = gender
                db.session.commit()
                bot_response_text = f"⚧️ Gender updated to: {gender}"
            else:
                bot_response_text = "Please specify gender as 'Male', 'Female', or 'Other'."
                next_state = 'profile_update_health_input'
        else:
            bot_response_text = "Specify either 'age' or 'gender' to update."
            next_state = 'profile_update_health_input'
    else:
        bot_response_text = "Patient profile not found or invalid input."

    bot_options = get_chatbot_options('profile_options')
    return bot_response_text, bot_options, next_state, chat_context
