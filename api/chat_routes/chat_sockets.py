from flask_socketio import emit, join_room, leave_room
from datetime import datetime

def init_socket_events(socketio, mongo):
    @socketio.on("join_room")
    def on_join(data):
        room = data.get("room")
        user = data.get("user")
        join_room(room)
        emit("notification", {"message": f"{user} has joined the room."}, to=room)

    @socketio.on("leave_room")
    def on_leave(data):
        room = data.get("room")
        user = data.get("user")
        leave_room(room)
        emit("notification", {"message": f"{user} has left the room."}, to=room)

    @socketio.on("send_message")
    def handle_message(data):
        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")
        message_content = data.get("message")
        role = data.get("role")

        # Save the message in MongoDB
        message_data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message": message_content,
            "role": role,
            "sent_at": datetime.utcnow(),
        }
        mongo.db.messages.insert_one(message_data)

        # Emit the message in real-time to the receiver's room
        emit(
            "receive_message",
            {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "message": message_content,
                "role": role,
                "sent_at": message_data["sent_at"].isoformat(),
            },
            to=receiver_id,
        )
