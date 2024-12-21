from api.ai_chat_bot_routes import chatbot


@chatbot.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.json.get('message')
    language = request.json.get('language', 'English')

    # Predict intent
    intent, confidence = predict_intent(user_input)

    # Fetch data based on intent
    if intent == "appointment":
        response = fetch_appointment()
    elif intent == "medication":
        response = "Here's your medication info..."
    else:
        response = "Sorry, I couldn't understand your query."

    return jsonify({"response": response, "intent": intent, "confidence": confidence})
