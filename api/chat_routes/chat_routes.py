from flask import Blueprint, request, jsonify
from datetime import datetime

from config import mongo
chat_routes = Blueprint("chat_routes", __name__)



@chat_routes.before_app_request
def setup_mongo():
    global mongo
    if mongo is None:  # Ensure mongo is initialized only once
        from app import mongo as app_mongo
        mongo = app_mongo

@chat_routes.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    message = data.get("message")
    role = data.get("role")

    if not sender_id or not receiver_id or not message:
        return jsonify({"error": "Sender, receiver, and message are required"}), 400

    # Save message to MongoDB
    message_data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": message,
        "role": role,
        "sent_at": datetime.utcnow(),
    }
    result = mongo.db.messages.insert_one(message_data)

    # Return the message with _id automatically serialized
    message_data["_id"] = str(result.inserted_id)
    return jsonify(message_data), 200


@chat_routes.route("/get_messages/<receiver_id>", methods=["GET"])
def get_messages(receiver_id):
    role = request.args.get("role")
    query = {"receiver_id": receiver_id}
    if role:
        query["role"] = role

    messages = mongo.db.messages.find(query)
    message_list = [
        {
            "sender_id": msg["sender_id"],
            "message": msg["message"],
            "role": msg["role"],
            "sent_at": msg["sent_at"],
        }
        for msg in messages
    ]
    return jsonify(message_list), 200
