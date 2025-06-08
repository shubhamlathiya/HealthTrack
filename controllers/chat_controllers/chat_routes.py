from datetime import datetime

from flask import jsonify, render_template, redirect, url_for, request
from flask_socketio import emit, join_room, leave_room

from app import socketio  # Assuming 'app' is your Flask app instance
from controllers.chat_controllers import chat
from middleware.auth_middleware import token_required
from models.chatModel import Message, Notification, CommunicationRequest
from models.doctorModel import Doctor
from models.patientModel import Patient
from models.userModel import User, UserRole
from utils.config import db


# Helper function
def get_conversation_room(user1_id, user2_id):
    """Generate a consistent room ID for a conversation between two users"""
    ids = sorted([str(user1_id), str(user2_id)])
    return f"conversation_{'_'.join(ids)}"


def get_user_full_name(user_id, role_enum_or_str):
    """Helper to get full name based on user role."""
    # Convert role string to enum if necessary
    role_enum = UserRole(role_enum_or_str) if isinstance(role_enum_or_str, str) else role_enum_or_str

    if role_enum == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=user_id).first()
        if patient:
            return f"{patient.first_name} {patient.last_name}"
    elif role_enum == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if doctor:
            return f"{doctor.first_name} {doctor.last_name}"
    elif role_enum == UserRole.ADMIN:
        # For admin, you might have a default name or fetch from User model
        user = User.query.get(user_id)
        return user.email.split('@')[0] if user else "Admin"  # Use email prefix as a fallback name
    elif role_enum in [UserRole.DEPARTMENT_HEAD, UserRole.NURSE]:
        user = User.query.get(user_id)
        # Assuming you might want to fetch names from a profile linked to these roles if they exist
        # For now, default to email prefix
        return user.email.split('@')[0] if user else role_enum.value.capitalize()
    return "Unknown User"


# WebSocket Handlers
@socketio.on('connect')
def handle_connect():
    # user_id should ideally come from a secure session or token, not request.args for connect
    # For now, keeping as is but recommend a more robust authentication
    user_id = request.args.get('user_id')
    if user_id:
        join_room(user_id)  # Join user's personal room
        print(f'User {user_id} connected')


@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.args.get('user_id')  # Still problematic for reliable session management
    if user_id:
        print(f'User {user_id} disconnected')


@socketio.on('cancel_communication_request')
def handle_cancel_request(data):
    request_id = data.get('request_id')
    user_id = data.get('user_id')  # The user who initiated the cancel (should be sender)

    try:
        request_obj = CommunicationRequest.query.get(request_id)
        if not request_obj:
            emit('error', {'message': 'Request not found'}, room=user_id)
            return

        if str(request_obj.sender_id) != str(user_id):  # Ensure string comparison for IDs
            emit('error', {'message': 'Unauthorized to cancel this request'}, room=user_id)
            return

        if request_obj.status != 'pending':
            emit('error', {'message': 'Request already processed, cannot cancel'}, room=user_id)
            return

        receiver_id = request_obj.receiver_id
        sender_name = get_user_full_name(request_obj.sender_id, request_obj.sender_role)

        # Delete the request
        db.session.delete(request_obj)
        db.session.commit()

        # Notify receiver
        emit('communication_request_cancelled', {
            'request_id': request_id,
            'sender_id': request_obj.sender_id,
            'sender_name': sender_name,
            'message': f'Communication request from {sender_name} was cancelled.'
        }, room=receiver_id)

        # Notify sender of success
        emit('communication_request_cancelled', {
            'request_id': request_id,
            'sender_id': request_obj.sender_id,
            'message': 'Your communication request has been cancelled.'
        }, room=user_id)  # Send confirmation to the cancelling user

    except Exception as e:
        print(f"Error handling cancel communication request: {e}")
        emit('error', {'message': f'Error cancelling request: {str(e)}'}, room=user_id)


@socketio.on('join')
def handle_join(data):
    user_id = data.get('user_id')
    room = data.get('room')
    if user_id and room:
        join_room(room)
        print(f'User {user_id} joined room {room}')
        # No need to emit 'join_response' unless specific UI feedback is needed on join
        # emit('join_response', {'data': f'Joined room {room}'}, room=room)


@socketio.on('leave')
def handle_leave(data):
    user_id = data.get('user_id')
    room = data.get('room')
    if user_id and room:
        leave_room(room)
        print(f'User {user_id} left room {room}')
        # No need to emit 'leave_response'
        # emit('leave_response', {'data': f'Left room {room}'}, room=room)


@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    message_content = data.get('message')  # Renamed to avoid conflict with Message model

    if not all([sender_id, receiver_id, message_content]):
        # Emit error back to sender if data is incomplete
        emit('error', {'message': 'Missing message data'}, room=sender_id)
        return

    try:
        sender = User.query.get(sender_id)
        receiver = User.query.get(receiver_id)

        if not sender or not receiver:
            emit('error', {'message': 'Sender or receiver not found'}, room=sender_id)
            return

        # Check for existing accepted communication
        # This prevents direct messages between users who haven't accepted a request, if that's a policy
        # However, the current logic of `get_users_for_communication` implies direct chat is allowed
        # after an accepted request OR a prior message.
        # For simplicity, we'll allow message if users exist.

        # Create and save message
        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message_content,
            read_status=False  # Messages are unread by default when sent
        )
        db.session.add(new_message)
        db.session.commit()

        sender_full_name = get_user_full_name(sender.id, sender.role)
        receiver_full_name = get_user_full_name(receiver.id, receiver.role)

        # Broadcast the message to the conversation room
        conversation_room = get_conversation_room(sender_id, receiver_id)
        emit('receive_message', {
            'id': new_message.id,
            'sender_id': new_message.sender_id,
            'receiver_id': new_message.receiver_id,
            'message': new_message.message,
            'sent_at': new_message.sent_at.isoformat(),
            'sender_name': sender_full_name,
            'read_status': new_message.read_status  # Include read status
        }, room=conversation_room)  # Emit to both sender and receiver in the room

        # Create notification for the receiver
        notification = Notification(
            user_id=receiver_id,
            message=f"New message from {sender_full_name}",
            type="message",
            # Redirect to the specific chat. Frontend should pick up receiver_id.
            redirect_url=f"/chat/chat?receiver_id={sender_id}",
            read_status=False  # New notifications are unread by default
        )
        db.session.add(notification)
        db.session.commit()

        # Notify receiver's personal room of new notification
        emit('new_notification', {
            'id': notification.id,
            'message': notification.message,
            'type': notification.type,
            'redirect_url': notification.redirect_url,
            'created_at': notification.created_at.isoformat(),
            'read_status': notification.read_status
        }, room=receiver_id)

    except Exception as e:
        db.session.rollback()  # Rollback on error
        print(f"Error handling message: {str(e)}")
        emit('error', {'message': f"Failed to send message: {str(e)}"}, room=sender_id)


# Removed the redundant HTTP /send-message route as it's now handled by WebSocket

# --- HTTP Routes ---
@chat.route('/mark-messages-read', methods=['POST'])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def mark_messages_read(current_user):  # current_user is the ID here
    # Sender_id is the user who *sent* the messages that current_user is reading
    sender_id_param = request.args.get('sender_id')
    # Or, if using body JSON: sender_id_param = request.json.get('sender_id')
    if not sender_id_param:
        return jsonify({"error": "Missing sender_id"}), 400

    try:
        # Convert to int for comparison with integer IDs
        sender_id_int = int(sender_id_param)
        current_user_int = int(current_user)

        # Mark messages where the `sender_id` is the person who sent the messages,
        # and `receiver_id` is the `current_user`, and `read_status` is False.
        messages_to_update = Message.query.filter_by(
            sender_id=sender_id_int,
            receiver_id=current_user_int,
            read_status=False
        ).all()

        updated_message_ids = []
        if messages_to_update:
            for msg in messages_to_update:
                msg.read_status = True
                updated_message_ids.append(msg.id)
            db.session.commit()

            # Notify the original sender (sender_id_int) that their messages have been read
            # Emit to the sender's personal room.
            socketio.emit('messages_marked_as_read', {
                'reader_id': current_user_int,
                'sender_id': sender_id_int,
                'conversation_partner_id': current_user_int,  # The other user in the conversation
                'read_message_ids': updated_message_ids,
                'message': f'Messages from {current_user_int} to {sender_id_int} marked as read by {current_user_int}'
            }, room=sender_id_int)  # Emit to the sender's personal room

        return jsonify({"message": "Messages marked as read", "marked_count": len(updated_message_ids)}), 200

    except ValueError:
        db.session.rollback()
        return jsonify({"error": "Invalid sender_id or receiver_id format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@chat.route("/get-conversation", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_conversation(current_user):  # current_user is the ID
    # For a conversation, the 'sender_id' in the client query refers to the other user
    # in the conversation, not necessarily the actual sender of the message.
    # So, here 'user1_id' will be `current_user` and 'user2_id' will be `receiver_id`.
    user1_id = int(current_user)
    user2_id_param = request.args.get("user2_id")

    if not user2_id_param:
        return jsonify({"error": "user2_id (receiver_id) is required."}), 400

    try:
        user2_id = int(user2_id_param)

        messages = Message.query.filter(
            ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
            ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
        ).order_by(Message.sent_at.asc()).all()

        message_list = []
        for msg in messages:
            # Determine sender's full name
            sender_user = User.query.get(msg.sender_id)
            sender_full_name = get_user_full_name(sender_user.id, sender_user.role)

            message_list.append({
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "message": msg.message,
                "read_status": msg.read_status,
                "sent_at": msg.sent_at.isoformat(),
                "sender_name": sender_full_name
            })

        return jsonify({"conversation": message_list}), 200

    except ValueError:
        return jsonify({"error": "Invalid user ID format."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/get-users-for-communication", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_users_for_communication(current_user_id):  # Renamed for clarity current_user_id (int)
    try:
        # Get users who have communicated with the current user via messages
        sent_to = db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id).distinct()
        received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id).distinct()

        # Get users who have an accepted communication request with the current user
        # sender_id is the current_user_id, receiver_id is the other person
        accepted_sent_requests = db.session.query(CommunicationRequest.receiver_id).filter_by(
            sender_id=current_user_id, status='accepted').distinct()
        # receiver_id is the current_user_id, sender_id is the other person
        accepted_received_requests = db.session.query(CommunicationRequest.sender_id).filter_by(
            receiver_id=current_user_id, status='accepted').distinct()

        # Combine unique user IDs from messages and accepted communication requests
        user_ids = {user_id for (user_id,) in
                    sent_to.union(received_from).union(accepted_sent_requests).union(accepted_received_requests).all()}

        # Filter out the current user and get the details of other users
        users = User.query.filter(User.id.in_(user_ids), User.id != current_user_id, User.status == True).all()

        user_list = []

        # For each user, fetch conversation details
        for user in users:
            # Get the last message in the conversation with this user
            last_message_query = db.session.query(Message).filter(
                ((Message.sender_id == current_user_id) & (Message.receiver_id == user.id)) |
                ((Message.sender_id == user.id) & (Message.receiver_id == current_user_id))
            ).order_by(Message.sent_at.desc()).first()

            # Count unread messages from this user (messages where THEY are sender, YOU are receiver, and not read)
            unread_count = db.session.query(Message).filter_by(
                sender_id=user.id,
                receiver_id=current_user_id,
                read_status=False
            ).count()

            # Fetch the user's full name based on their role
            full_name = get_user_full_name(user.id, user.role)

            user_list.append({
                "id": user.id,
                "name": full_name,
                "email": user.email,
                "role": user.role.value,  # Ensure it's the string value of the enum
                "last_message": last_message_query.message if last_message_query else None,
                "last_message_time": last_message_query.sent_at.isoformat() if last_message_query else None,
                "unread_count": unread_count
            })

        # Sort user list by latest message time, if available, otherwise by name
        user_list.sort(key=lambda x: x['last_message_time'] if x['last_message_time'] else '0', reverse=True)

        return jsonify(user_list), 200

    except Exception as e:
        print(f"Error in get_users_for_communication: {e}")
        return jsonify({"error": str(e)}), 500


@chat.route("/get-notifications", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_notifications(current_user_id):  # Renamed for clarity
    try:
        notifications = Notification.query.filter_by(user_id=current_user_id).order_by(
            Notification.created_at.desc()).all()

        notification_list = [{
            "id": notif.id,
            "message": notif.message,
            "created_at": notif.created_at.isoformat(),
            "read_status": notif.read_status,
            "redirect_url": notif.redirect_url
        } for notif in notifications]

        return jsonify(notification_list), 200

    except Exception as e:
        print(f"Error in get_notifications: {e}")
        return jsonify({"error": str(e)}), 500


@chat.route("/mark-notification-as-read/<int:notification_id>", methods=["PUT"])
@token_required(  # Add token_required here as well
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def mark_notification_as_read(current_user, notification_id):  # Added current_user_id
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({"error": "Notification not found"}), 404
        print(type(notification.user_id))
        print(type(current_user))
        # Ensure only the owner can mark their notification as read
        if notification.user_id != int(current_user):
            return jsonify({"error": "Unauthorized to mark this notification as read"}), 403

        notification.read_status = True
        db.session.commit()

        return jsonify({"message": "Notification marked as read"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error in mark_notification_as_read: {e}")
        return jsonify({"error": str(e)}), 500


@chat.route("/mark-all-notifications-as-read", methods=["PUT"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def mark_all_notifications_as_read(current_user_id):
    try:
        # Mark all unread notifications for the current user as read
        notifications_to_update = Notification.query.filter_by(
            user_id=current_user_id,
            read_status=False
        ).all()

        if notifications_to_update:
            for notif in notifications_to_update:
                notif.read_status = True
            db.session.commit()

        return jsonify({"message": "All notifications marked as read"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error in mark_all_notifications_as_read: {e}")
        return jsonify({"error": str(e)}), 500


@chat.route("/send-communication-request", methods=["POST"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def send_communication_request(current_user_id):  # Renamed for clarity
    """Send a communication request to another user"""
    data = request.json
    receiver_id = data.get("receiver_id")
    message = data.get("message", "").strip()

    if not receiver_id:
        return jsonify({"error": "Receiver ID is required"}), 400

    try:
        # Check if receiver exists
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({"error": "Receiver not found"}), 404

        # Prevent sending request to self
        if int(receiver_id) == int(current_user_id):
            return jsonify({"error": "Cannot send a communication request to yourself"}), 400

        # Check if a pending request already exists in either direction
        existing_request_sender = CommunicationRequest.query.filter_by(
            sender_id=current_user_id,
            receiver_id=receiver_id,
            status='pending'
        ).first()
        existing_request_receiver = CommunicationRequest.query.filter_by(
            sender_id=receiver_id,
            receiver_id=current_user_id,
            status='pending'
        ).first()

        if existing_request_sender or existing_request_receiver:
            return jsonify({"error": "A pending request between these users already exists"}), 400

        # Check if a conversation (accepted request or existing message) already exists
        # This prevents sending requests if they can already chat
        conversation_exists = Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user_id))
        ).first()
        accepted_comm_exists = CommunicationRequest.query.filter(
            ((CommunicationRequest.sender_id == current_user_id) & (CommunicationRequest.receiver_id == receiver_id)) |
            ((CommunicationRequest.sender_id == receiver_id) & (CommunicationRequest.receiver_id == current_user_id))
        ).filter_by(status='accepted').first()

        if conversation_exists or accepted_comm_exists:
            return jsonify({"error": "Conversation already established with this user"}), 400

        # Create new request
        new_request = CommunicationRequest(
            sender_id=current_user_id,
            receiver_id=receiver_id,
            message=message,
            status='pending',
            sender_role=User.query.get(current_user_id).role  # Store sender's role
        )
        db.session.add(new_request)
        db.session.commit()

        sender_user = User.query.get(current_user_id)
        sender_full_name = get_user_full_name(sender_user.id, sender_user.role)

        # Send WebSocket notification to the receiver's personal room
        socketio.emit('new_communication_request', {
            'request_id': new_request.id,
            'sender_id': current_user_id,
            'sender_name': sender_full_name,
            'receiver_id': receiver_id,
            'message': message,
            'created_at': new_request.created_at.isoformat()
        }, room=receiver_id)

        # Create a notification record for the receiver as well
        notification = Notification(
            user_id=receiver_id,
            message=f"New communication request from {sender_full_name}",
            type="communication_request",
            redirect_url="/chat/get-pending-requests"  # Or a direct link to the requests modal
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({
            "message": "Communication request sent",
            "request_id": new_request.id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error sending communication request: {e}")
        return jsonify({"error": str(e)}), 500


@chat.route("/respond-to-request/<int:request_id>", methods=["POST"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def respond_to_communication_request(current_user_id, request_id):  # Renamed for clarity
    try:
        data = request.json
        action = data.get("action")  # 'accept' or 'reject'

        if action not in ['accept', 'reject']:
            return jsonify({"error": "Invalid action"}), 400

        communication_request = CommunicationRequest.query.get(request_id)
        if not communication_request:
            return jsonify({"error": "Request not found"}), 404

        # Ensure the current user is the actual receiver of this request
        if communication_request.receiver_id != current_user_id:
            return jsonify({"error": "Unauthorized to respond to this request"}), 403

        # Check if the request is already processed
        if communication_request.status != 'pending':
            return jsonify({"error": "Request already processed"}), 400

        communication_request.status = 'accepted' if action == 'accept' else 'rejected'
        db.session.commit()

        sender_user = User.query.get(communication_request.sender_id)
        receiver_user = User.query.get(current_user_id)  # The current user is the receiver

        sender_full_name = get_user_full_name(sender_user.id, sender_user.role)
        receiver_full_name = get_user_full_name(receiver_user.id, receiver_user.role)

        # Notify the sender about the response to their request
        socketio.emit('communication_request_response', {
            'request_id': communication_request.id,
            'sender_id': current_user_id,  # The responder is the sender of this event
            'receiver_id': communication_request.sender_id,  # The original sender is the receiver of this event
            'status': communication_request.status,
            'responded_at': datetime.utcnow().isoformat(),
            'message': f'{receiver_full_name} has {action}ed your communication request.'
        }, room=communication_request.sender_id)  # Emit to the original sender's personal room

        # If accepted, create and send a welcome message from receiver to sender
        if action == 'accept':
            welcome_msg = f"Hello {sender_full_name}! I've accepted your communication request. How can I help you?"

            new_message = Message(
                sender_id=current_user_id,  # current_user is the sender of this welcome message
                receiver_id=communication_request.sender_id,  # Original sender is the receiver
                message=welcome_msg,
                read_status=False
            )
            db.session.add(new_message)
            db.session.commit()

            conversation_room = get_conversation_room(current_user_id, communication_request.sender_id)
            socketio.emit('receive_message', {
                'id': new_message.id,
                'sender_id': new_message.sender_id,
                'receiver_id': new_message.receiver_id,
                'message': new_message.message,
                'sent_at': new_message.sent_at.isoformat(),
                'sender_name': receiver_full_name,
                'read_status': new_message.read_status
            }, room=conversation_room)

            # Create a notification for the original sender about the welcome message
            notification = Notification(
                user_id=communication_request.sender_id,
                message=f"Your communication request was accepted by {receiver_full_name}",
                type="message",
                redirect_url=f"/chat/chat?receiver_id={current_user_id}"
            )
            db.session.add(notification)
            db.session.commit()

            socketio.emit('new_notification', {
                'id': notification.id,
                'message': notification.message,
                'type': notification.type,
                'redirect_url': notification.redirect_url,
                'created_at': notification.created_at.isoformat(),
                'read_status': notification.read_status
            }, room=communication_request.sender_id)

        return jsonify({
            "message": f"Request {action}ed",
            "status": communication_request.status,
            "sender_id": communication_request.sender_id  # Return the ID of the chat partner
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error responding to request: {e}")
        return jsonify({"error": str(e)}), 500


@chat.route("/get-pending-requests", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_pending_requests(current_user_id):  # Renamed for clarity
    """Get pending communication requests for current user"""
    try:
        # Filter by receiver_id, as current_user is the receiver of these requests
        requests = CommunicationRequest.query.filter_by(
            receiver_id=current_user_id,
            status='pending'
        ).join(User, CommunicationRequest.sender_id == User.id).add_columns(
            CommunicationRequest.id.label('request_id'),
            CommunicationRequest.sender_id,
            CommunicationRequest.message,
            CommunicationRequest.created_at,
            User.email,
            User.role
        ).order_by(CommunicationRequest.created_at.desc()).all()

        request_list = []

        for req in requests:
            sender_id = req.sender_id
            role = req.role  # This is already an Enum, no need for .value here initially

            # Get sender name based on role
            sender_name = get_user_full_name(sender_id, role)

            request_list.append({
                "request_id": req.request_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_email": req.email,
                "sender_role": role.value,  # Send as string to frontend
                "message": req.message,
                "created_at": req.created_at.isoformat()
            })

        return jsonify(request_list), 200

    except Exception as e:
        print(f"Error in get_pending_requests: {e}")
        return jsonify({"error": str(e)}), 500


@chat.route("/get-unread-notification-count", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_unread_notification_count(current_user):  # Renamed for clarity
    """Get the count of unread notifications and messages for the current user"""
    try:
        # Count unread messages where current_user_id is the receiver and read_status is False
        unread_messages_count = Message.query.filter_by(
            receiver_id=current_user,
            read_status=False
        ).count()

        # Count unread notifications for the current user
        unread_notifications_count = Notification.query.filter_by(
            user_id=current_user,
            read_status=False
        ).count()

        # Count pending communication requests received by the current user
        pending_requests_count = CommunicationRequest.query.filter_by(
            receiver_id=current_user,
            status='pending'
        ).count()

        # Calculate total unread count (messages + notifications + requests)
        total_unread_count = unread_messages_count + unread_notifications_count + pending_requests_count

        return jsonify({
            "count": total_unread_count,
            "message_count": unread_messages_count,
            "notification_count": unread_notifications_count,
            "request_count": pending_requests_count,  # Include request count
            "message": "Unread counts retrieved successfully"
        }), 200

    except Exception as e:
        print(f"Error in get_unread_notification_count: {e}")
        return jsonify({
            "error": str(e),
            "message": "Failed to get unread counts"
        }), 500


@chat.route("/get-potential-recipients", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_potential_recipients(current_user):  # Renamed for clarity
    """Get a list of users that the current user can potentially start a conversation with"""
    try:
        current_user_obj = User.query.get(current_user)
        if not current_user_obj:
            return jsonify({"error": "User not found"}), 404

        potential_recipients_query = User.query.filter(User.id != current_user, User.status == True)

        if current_user_obj.role == UserRole.ADMIN:
            # Admin can see all users
            pass
        elif current_user_obj.role == UserRole.PATIENT:
            # Patient can only see doctors
            potential_recipients_query = potential_recipients_query.filter(User.role == UserRole.DOCTOR)
        elif current_user_obj.role == UserRole.DOCTOR:
            # Doctor can see all users
            pass
        elif current_user_obj.role in [UserRole.DEPARTMENT_HEAD, UserRole.NURSE]:
            # Define specific rules for DEP HEAD and NURSE if needed
            # For now, let's say they can communicate with DOCTORs and PATIENTs
            potential_recipients_query = potential_recipients_query.filter(
                (User.role == UserRole.DOCTOR) | (User.role == UserRole.PATIENT)
            )
        else:
            potential_recipients_query = potential_recipients_query.filter(User.id == -1)  # No users

        potential_recipients = potential_recipients_query.all()

        recipient_list = []
        for user in potential_recipients:
            # Check if there's an existing accepted communication request or message history
            conversation_exists = Message.query.filter(
                ((Message.sender_id == current_user) & (Message.receiver_id == user.id)) |
                ((Message.sender_id == user.id) & (Message.receiver_id == current_user))
            ).first()
            accepted_comm_exists = CommunicationRequest.query.filter(
                ((CommunicationRequest.sender_id == current_user) & (CommunicationRequest.receiver_id == user.id)) |
                ((CommunicationRequest.sender_id == user.id) & (CommunicationRequest.receiver_id == current_user))
            ).filter_by(status='accepted').first()

            # Only add users with whom no active conversation or accepted request exists
            if not conversation_exists and not accepted_comm_exists:
                user_data = {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role.value,
                    "first_name": "",  # Initialize for safety
                    "last_name": "",  # Initialize for safety
                }

                # Add specific details if available
                if user.role == UserRole.DOCTOR:
                    doctor = Doctor.query.filter_by(user_id=user.id).first()
                    if doctor:
                        user_data["first_name"] = doctor.first_name
                        user_data["last_name"] = doctor.last_name
                        # user_data.update({ ... other doctor specific fields ...})
                elif user.role == UserRole.PATIENT:
                    patient = Patient.query.filter_by(user_id=user.id).first()
                    if patient:
                        user_data["first_name"] = patient.first_name
                        user_data["last_name"] = patient.last_name
                        # user_data.update({ ... other patient specific fields ...})
                elif user.role == UserRole.ADMIN:
                    user_data["first_name"] = "Admin"
                    user_data["last_name"] = ""  # No last name for generic admin
                elif user.role in [UserRole.DEPARTMENT_HEAD, UserRole.NURSE]:
                    # Assuming these roles might not have separate profiles, use email prefix
                    user_data["first_name"] = user.email.split('@')[0]
                    user_data["last_name"] = ""

                recipient_list.append(user_data)

        return jsonify(recipient_list), 200

    except Exception as e:
        print(f"Error in get_potential_recipients: {e}")
        return jsonify({"error": str(e)}), 500


@chat.route("/chat", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def chat_ui(current_user):  # Renamed for clarity
    print("Current User ID:", current_user)

    receiver_id = request.args.get('receiver_id')
    receiver_name = None
    receiver_role = None

    # Fetch the actual current_user object to pass to the template
    current_user_obj = User.query.get(current_user)
    if not current_user_obj:
        # Handle case where current user is not found (shouldn't happen with token_required)
        return "User not found", 404

    if receiver_id:
        receiver = User.query.filter_by(id=receiver_id).first()
        if receiver:
            receiver_name = get_user_full_name(receiver.id, receiver.role)
            receiver_role = receiver.role.value
        else:
            receiver_name = "Unknown"
            receiver_role = "Unknown"
            receiver_id = None  # Clear receiver_id if not found, to show empty state

    return render_template(
        "chat_templates/ch.html",
        current_user=current_user_obj,  # Pass the User object
        receiver_id=receiver_id,
        receiver_name=receiver_name,
        receiver_role=receiver_role
    )