from controllers.chat_bot_controllers.utils.helper_funcation import get_chatbot_options


def handle_faq_help(user_obj, data, chat_context):
    user_selection_value = data.get('selection_value')
    bot_response_text = ""
    bot_options = []
    next_state = 'faq_help'  # Keep in this state if offering sub-options, otherwise go back to main_menu

    if user_selection_value == 'faq_help':  # Initial entry into FAQ state
        bot_response_text = (
            "👋 Welcome to the Help Center! Here are some common questions I can help with:\n\n"
            "1️⃣ **How do I request an ambulance?**\n"
            "   ➤ Select *'Request Ambulance'* from the main menu and follow the steps.\n\n"
            "2️⃣ **How do I order medicine?**\n"
            "   ➤ Choose *'Request Medicine'* and enter your prescription details or search by name.\n\n"
            "3️⃣ **Can I track my request?**\n"
            "   ➤ You can view the status of your last ambulance call from the main menu.\n"
            "   ➤ For detailed tracking or help, feel free to speak with a support agent.\n\n"
            "❓ What would you like to know more about, or would you like to return to the 🏠 Main Menu?"
        )

        bot_options = get_chatbot_options('faq_options')  # Offer specific FAQ topics or 'Main Menu'
        next_state = 'faq_help'  # Stay in FAQ flow if offering options
    elif user_selection_value == 'faq_ambulance_request':
        bot_response_text = (
            "🚑 To request an ambulance, go to the 🏠 *Main Menu* and select **'Request Ambulance'**.\n\n"
            "You’ll be guided to:\n"
            "• Select the type of emergency (e.g., Chest Pain, Accident, etc.)\n"
            "• Confirm or enter your pickup location\n\n"
            "Would you like to know anything else about ambulance requests?"
        )

        bot_options = get_chatbot_options('faq_options')
        next_state = 'faq_help'
    elif user_selection_value == 'faq_medicine_order':
        bot_response_text = (
            "💊 To order medicine, go to the 🏠 *Main Menu* and select **'Request Medicine'**.\n\n"
            "You’ll be asked to:\n"
            "• Enter the medicine name and quantity\n"
            "• Provide or confirm your delivery address\n"
            "• (Optional) Upload a valid prescription if required\n\n"
            "Is there anything else you'd like to know about placing a medicine order?"
        )

        bot_options = get_chatbot_options('faq_options')
        next_state = 'faq_help'
    elif user_selection_value == 'faq_operating_hours':
        bot_response_text = (
            "🕒 Our services are available as follows:\n\n"
            "🚑 **Emergency Ambulance Requests** – Available 24/7\n"
            "💊 **Medicine Delivery** – Typically available from 8:00 AM to 10:00 PM, depending on pharmacy availability\n\n"
            "Is there anything else you'd like to ask?"
        )

        bot_options = get_chatbot_options('faq_options')
        next_state = 'faq_help'
    elif user_selection_value == 'main_menu':  # Option to return to main menu
        bot_response_text = "Returning to the main menu. How can I help you further?"
        bot_options = get_chatbot_options('main_menu_options')
        next_state = 'main_menu_options'
    else:
        # Fallback if an unrecognized selection or direct message in FAQ state
        bot_response_text = (
            "😕 Sorry, I didn't catch that. Please choose one of the available options below, "
            "or type **'Main Menu'** to start over."
        )

        bot_options = get_chatbot_options('faq_options')
        next_state = 'faq_help'

    return bot_response_text, bot_options, next_state, chat_context
