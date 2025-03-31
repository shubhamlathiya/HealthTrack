from bson import ObjectId
from flask import Blueprint, request, jsonify, render_template, redirect
from datetime import datetime
from utils.config import mongo
from middleware.auth_middleware import token_required

# Create a blueprint for chat routes
chat_routes = Blueprint("chat_routes", __name__)


# Send a message and save it to MongoDB
@chat_routes.route("/send-message", methods=["POST"])
def send_message():
    """Send a message and save it to MongoDB."""
    data = request.json
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    message = data.get("message")

    # print(data)
    # Validate that all required fields are provided
    if not sender_id or not receiver_id or not message:
        return jsonify({"error": "Sender, receiver, and message are required"}), 400

    # Prepare the message data for MongoDB, convert ObjectId to proper format
    message_data = {
        "sender_id": ObjectId(sender_id),
        "receiver_id": ObjectId(receiver_id),
        "message": message,
        "read_status": False,
        "sent_at": datetime.utcnow(),
    }

    # Insert the message into MongoDB
    result = mongo.db.messages.insert_one(message_data)

    # Fetch the inserted message and prepare the response data
    message_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string

    # Construct response to send back, converting ObjectId and datetime to string
    response_data = {
        'sender_id': str(message_data["sender_id"]),
        'receiver_id': str(message_data["receiver_id"]),
        'message': message_data["message"],
        'sent_at': message_data["sent_at"].isoformat(),  # Convert datetime to ISO string
        '_id': message_data["_id"]
    }

    redirect_url = f"/chat/{sender_id}/{receiver_id}"

    # Now add the notification for the receiver
    notification_data = {
        "user_id": ObjectId(receiver_id),
        "message": f"You have a new message from {sender_id}",
        "type": "message",
        "created_at": datetime.utcnow(),
        "read_status": False,  # Set as unread by default
        "redirect_url": redirect_url  # Include the URL for redirection
    }

    # Insert the notification into the notifications collection
    mongo.db.notifications.insert_one(notification_data)

    # Return the response data as JSON
    return jsonify(response_data), 200


# Retrieve messages for a given receiver ID
@chat_routes.route("/get-messages/<receiver_id>", methods=["GET"])
def get_messages(receiver_id):
    """Retrieve messages for a given receiver ID."""

    query = {"receiver_id": receiver_id}

    messages = mongo.db.messages.find(query)
    message_list = [
        {
            "sender_id": msg["sender_id"],
            "message": msg["message"],
            "sent_at": msg["sent_at"],
        }
        for msg in messages
    ]
    return jsonify(message_list), 200


# Additional route to retrieve messages for a specific sender and receiver
@chat_routes.route("/get-conversation", methods=["GET"])
def get_conversation():
    """Retrieve the full conversation between a sender and receiver."""
    sender_id = ObjectId(request.args.get("sender_id"))
    receiver_id = ObjectId(request.args.get("receiver_id"))

    if not sender_id or not receiver_id:
        return jsonify({"error": "Sender and receiver are required."}), 400

    messages = mongo.db.messages.find(
        {"$or": [{"sender_id": sender_id, "receiver_id": receiver_id},
                 {"sender_id": receiver_id, "receiver_id": sender_id}]}
    ).sort("sent_at", 1)  # Sorting by sent_at to get the conversation in order

    message_list = [
        {
            "sender_id": str(msg["sender_id"]),
            "receiver_id": str(msg["receiver_id"]),
            "message": msg["message"],
            "sent_at": msg["sent_at"],
        }
        for msg in messages
    ]
    return jsonify(message_list), 200


@chat_routes.route("/chat", methods=["GET"])
@token_required
def chat(current_user):
    return render_template("chat_templates/chat_application_templates.html", current_user=current_user)


@chat_routes.route("/start-conversation/<receiver_id>", methods=["GET"], endpoint="start_conversation")
@token_required
def start_conversation(current_user, receiver_id):
    # Check if receiver exists
    existing_receiver = mongo.db.users.find_one({'_id': ObjectId(receiver_id)})

    if not existing_receiver:
        return jsonify({'error': 'Receiver not found'}), 404

    # Check if the user has already started a conversation with the receiver
    existing_conversation = mongo.db.messages.find_one({
        "$or": [
            {"sender_id": ObjectId(current_user), "receiver_id": ObjectId(receiver_id)},
            {"sender_id": ObjectId(receiver_id), "receiver_id": ObjectId(current_user)}
        ]
    })

    if existing_conversation:
        return redirect('/chat/chat')

    # Determine the role-based message
    if existing_receiver["role"] == "patient":
        message = "Hi, I am a doctor. How can I help you?"
        sender_id = current_user
    else:
        message = "Hi, I am a patient."
        sender_id = current_user

    # Send the default message
    send_message_to_doctor(sender_id, receiver_id, message)

    # Respond with success message and redirect to chat
    return redirect('/chat/chat')


def send_message_to_doctor(sender_id, receiver_id, message):
    """
    This function would handle the logic of sending a message between users
    (e.g., save the message in the database).
    """
    message_data = {
        "sender_id": ObjectId(sender_id),
        "receiver_id": ObjectId(receiver_id),
        "message": message,
        "sent_at": datetime.utcnow(),
    }

    # Insert the message into MongoDB
    result = mongo.db.messages.insert_one(message_data)

    print(f"Message from {sender_id} to {receiver_id}: {message}")
    # Implement the actual database insertion here


@chat_routes.route("/get-users-for-communication", methods=["GET"], endpoint="get_users_for_communication")
@token_required
def get_users_for_communication(current_user):
    """Retrieve all users that the current user (either sender or receiver) has communicated with."""

    # Check if the current user is the sender or receiver by querying the messages collection
    sender_communicated = mongo.db.messages.distinct("receiver_id", {"sender_id": ObjectId(current_user)})
    receiver_communicated = mongo.db.messages.distinct("sender_id", {"receiver_id": ObjectId(current_user)})

    # Combine both lists to avoid duplicates
    all_communicated_user_ids = list(set(sender_communicated + receiver_communicated))

    # Fetch the details of all unique users the current user has communicated with
    users = mongo.db.users.find({"_id": {"$in": [ObjectId(user_id) for user_id in all_communicated_user_ids]}})

    # Prepare the list of users (sender/receiver details) to send back in the response
    user_list = [
        {
            "_id": str(user["_id"]),  # Convert ObjectId to string
            "name": user.get("name"),  # Or any other field you want (e.g., email)
            "email": user.get("email")  # Example field
        }
        for user in users
    ]
    # print(user_list)

    return jsonify(user_list), 200


# Retrieve notifications for a given user ID
@chat_routes.route("/get-notifications", methods=["GET"], endpoint="get_notifications")
@token_required
def get_notifications(current_user):
    """Retrieve all notifications for a user."""

    # Query to find notifications for the user
    notifications = mongo.db.notifications.find({"user_id": ObjectId(current_user)}).sort("created_at", -1)

    notification_list = [
        {
            "message": notif["message"],
            "created_at": notif["created_at"],
            "read_status": notif["read_status"],
            "_id": str(notif["_id"]),  # Convert ObjectId to string
        }
        for notif in notifications
    ]

    return jsonify(notification_list), 200


# Mark a notification as read
@chat_routes.route("/mark-notification-as-read/<notification_id>", methods=["PUT"])
def mark_notification_as_read(notification_id):
    """Mark a notification as read."""

    # Update the notification's read status
    result = mongo.db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read_status": True}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Notification not found"}), 404

    return jsonify({"message": "Notification marked as read"}), 200


# Redirect to the URL from the notification
@chat_routes.route("/redirect-to-notification/<notification_id>", methods=["GET"])
def redirect_to_notification(notification_id):
    """Redirect the user to the page associated with the notification."""

    # Fetch the notification from the database using the notification_id
    notification = mongo.db.notifications.find_one({"_id": ObjectId(notification_id)})

    if not notification:
        return jsonify({"error": "Notification not found"}), 404

    # Get the redirect URL from the notification
    redirect_url = notification.get("redirect_url")

    # If no URL exists, return an error
    if not redirect_url:
        return jsonify({"error": "Redirect URL not available"}), 404

    # Redirect the user to the associated page
    return redirect(redirect_url)


@chat_routes.route("/<sender_id>/<receiver_id>", methods=["GET"])
def chat(sender_id, receiver_id):
    """Retrieve the chat between sender and receiver."""
    # Check if sender and receiver are valid
    if not sender_id or not receiver_id:
        return jsonify({"error": "Sender and receiver are required."}), 400

    # Convert sender and receiver IDs to ObjectId
    sender_id = ObjectId(sender_id)
    receiver_id = ObjectId(receiver_id)

    # Retrieve the conversation between sender and receiver
    messages = mongo.db.messages.find(
        {"$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id}
        ]}
    ).sort("sent_at", 1)  # Sorting messages by sent_at in ascending order

    message_list = [
        {
            "sender_id": str(msg["sender_id"]),
            "receiver_id": str(msg["receiver_id"]),
            "message": msg["message"],
            "sent_at": msg["sent_at"].isoformat(),  # Convert datetime to ISO format
        }
        for msg in messages
    ]

    # Return the conversation as a JSON response
    return jsonify({"conversation": message_list}), 200
