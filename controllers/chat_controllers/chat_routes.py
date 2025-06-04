from datetime import datetime

from flask import jsonify, render_template, redirect, url_for, request
from flask_socketio import emit, join_room, leave_room

from app import socketio
from controllers.chat_controllers import chat
from middleware.auth_middleware import token_required
from models.chatModel import Message, Notification, CommunicationRequest
from models.doctorModel import Doctor
from models.patientModel import Patient
from models.userModel import User, UserRole
from utils.config import db


# Helper function
def get_conversation_room(user1, user2):
    """Generate a consistent room ID for a conversation between two users"""
    ids = sorted([str(user1), str(user2)])
    return f"conversation_{'_'.join(ids)}"


# WebSocket Handlers
@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')
    if user_id:
        join_room(user_id)  # Join user's personal room
        print(f'User {user_id} connected')


@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.args.get('user_id')
    if user_id:
        print(f'User {user_id} disconnected')


@socketio.on('cancel_communication_request')
def handle_cancel_request(data):
    request_id = data.get('request_id')
    user_id = data.get('user_id')

    try:
        request = CommunicationRequest.query.get(request_id)
        if not request:
            emit('error', {'message': 'Request not found'})
            return

        if request.sender_id != user_id:
            emit('error', {'message': 'Unauthorized'})
            return

        if request.status != 'pending':
            emit('error', {'message': 'Request already processed'})
            return

        # Delete the request
        db.session.delete(request)
        db.session.commit()

        # Notify receiver
        emit('communication_request_cancelled', {
            'request_id': request_id,
            'sender_id': request.sender_id
        }, room=request.receiver_id)

    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('join')
def handle_join(data):
    user_id = data['user_id']
    room = data['room']
    join_room(room)
    print(f'User {user_id} joined room {room}')
    emit('join_response', {'data': f'Joined room {room}'}, room=room)


@socketio.on('leave')
def handle_leave(data):
    user_id = data['user_id']
    room = data['room']
    leave_room(room)
    print(f'User {user_id} left room {room}')
    emit('leave_response', {'data': f'Left room {room}'}, room=room)


@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    message = data['message']

    try:
        # Create and save message
        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message
        )
        db.session.add(new_message)
        db.session.commit()

        # Get sender name
        sender = User.query.get(sender_id)

        # Create notification
        notification = Notification(
            user_id=receiver_id,
            message=f"You have a new message from {sender.name}",
            type="message",
            redirect_url=f"/chat/{sender_id}/{receiver_id}"
        )
        db.session.add(notification)
        db.session.commit()

        # Broadcast the message to the room
        room = get_conversation_room(sender_id, receiver_id)
        emit('receive_message', {
            'id': new_message.id,
            'sender_id': new_message.sender_id,
            'receiver_id': new_message.receiver_id,
            'message': new_message.message,
            'sent_at': new_message.sent_at.isoformat(),
            'sender_name': sender.name
        }, room=room)

        # Notify receiver of new message if they're online
        emit('new_notification', {
            'message': f"You have a new message from {sender.name}",
            'redirect_url': f"/chat/{sender_id}/{receiver_id}"
        }, room=receiver_id)

    except Exception as e:
        print(f"Error handling message: {str(e)}")


# HTTP Routes
@chat.route("/send-message", methods=["POST"])
def send_message():
    data = request.json
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    message = data.get("message")

    if not sender_id or not receiver_id or not message:
        return jsonify({"error": "Sender, receiver, and message are required"}), 400

    try:
        # Trigger the WebSocket event
        socketio.emit('send_message', {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': message
        })

        return jsonify({"status": "Message sent"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route('/mark-messages-read', methods=['POST'])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def mark_messages_read(current_user):
    sender_id = request.args.get('sender_id')
    if not sender_id:
        return jsonify({"error": "Missing sender_id"}), 400

    Message.query.filter_by(sender_id=sender_id, receiver_id=current_user, read_status=False).update({"read_status": True})
    db.session.commit()
    return jsonify({"message": "Messages marked as read"}), 200


@chat.route("/get-conversation", methods=["GET"])
def get_conversation():
    sender_id = request.args.get("sender_id")
    receiver_id = request.args.get("receiver_id")

    if not sender_id or not receiver_id:
        return jsonify({"error": "Sender and receiver are required."}), 400

    try:
        messages = Message.query.filter(
            ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
        ).order_by(Message.sent_at.asc()).all()

        message_list = []
        for msg in messages:
            sender = User.query.get(msg.sender_id)
            full_name = get_user_full_name(sender.id, sender.role)
            message_list.append({
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "message": msg.message,
                "read_status": msg.read_status,
                "sent_at": msg.sent_at.isoformat(),
                "sender_name": full_name
            })

        return jsonify({"conversation": message_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/get-users-for-communication", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_users_for_communication(current_user):
    try:
        # Get users who have communicated with the current user via messages
        sent_to = db.session.query(Message.receiver_id).filter_by(sender_id=current_user).distinct()
        received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user).distinct()

        # Get users who have an accepted communication request with the current user
        accepted_requests = db.session.query(CommunicationRequest.sender_id).filter_by(
            receiver_id=current_user, status='accepted').distinct()
        accepted_requests_receiver = db.session.query(CommunicationRequest.receiver_id).filter_by(
            sender_id=current_user, status='accepted').distinct()

        # Combine user IDs from messages and accepted communication requests
        user_ids = {user_id for (user_id,) in
                    sent_to.union(received_from).union(accepted_requests).union(accepted_requests_receiver).all()}

        # Filter out the current user and get the details of other users
        users = User.query.filter(User.id.in_(user_ids), User.id != current_user).all()

        user_list = []

        # For each user, fetch conversation details
        for user in users:
            # Get the last message sent by the current user to this user
            last_sent_message = db.session.query(Message).filter_by(
                sender_id=current_user,
                receiver_id=user.id
            ).order_by(Message.sent_at.desc()).first()

            # Get the last message received from this user
            last_received_message = db.session.query(Message).filter_by(
                sender_id=user.id,
                receiver_id=current_user
            ).order_by(Message.sent_at.desc()).first()

            # Determine the most recent message (either sent or received)
            last_message = None
            if last_sent_message and last_received_message:
                last_message = last_sent_message if last_sent_message.sent_at > last_received_message.sent_at else last_received_message
            elif last_sent_message:
                last_message = last_sent_message
            elif last_received_message:
                last_message = last_received_message

            # Count unread messages from this user
            unread_count = db.session.query(Message).filter_by(
                sender_id=user.id,
                receiver_id=current_user,
                read_status=False
            ).count()

            # Fetch the user's full name based on their role
            full_name = get_user_full_name(user.id, user.role)

            user_list.append({
                "id": user.id,
                "name": full_name,
                "email": user.email,
                "role": user.role.value,
                "last_message": last_message.message if last_message else None,
                "last_message_time": last_message.sent_at.isoformat() if last_message else None,
                "unread_count": unread_count  # Add unread message count
            })

        return jsonify(user_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/get-notifications", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_notifications(current_user):
    try:
        notifications = Notification.query.filter_by(user_id=current_user).order_by(
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
        return jsonify({"error": str(e)}), 500


@chat.route("/mark-notification-as-read/<int:notification_id>", methods=["PUT"])
def mark_notification_as_read(notification_id):
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({"error": "Notification not found"}), 404

        notification.read_status = True
        db.session.commit()

        return jsonify({"message": "Notification marked as read"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/start-conversation/<int:receiver_id>", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def start_conversation(current_user, receiver_id):
    try:
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({'error': 'Receiver not found'}), 404

        # Check if conversation already exists
        existing_conversation = Message.query.filter(
            ((Message.sender_id == current_user) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user))
        ).first()

        if existing_conversation:
            return redirect(url_for('chat_routes.chat_ui', sender_id=current_user, receiver_id=receiver_id))

        # Determine the role-based message
        if receiver.role == "patient":
            message = "Hi, I am a doctor. How can I help you?"
        else:
            message = "Hi, I am a patient."

        # Send the default message via WebSocket
        socketio.emit('send_message', {
            'sender_id': current_user,
            'receiver_id': receiver_id,
            'message': message
        })

        return redirect(url_for('chat_routes.chat_ui', sender_id=current_user, receiver_id=receiver_id))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/send-communication-request", methods=["POST"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def send_communication_request(current_user):
    """Send a communication request to another user"""
    data = request.json
    receiver_id = data.get("receiver_id")
    message = data.get("message", "")

    print(receiver_id)
    if not receiver_id:
        return jsonify({"error": "Receiver ID is required"}), 400

    try:
        # Check if receiver exists
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({"error": "Receiver not found"}), 404

        # Check if request already exists
        existing_request = CommunicationRequest.query.filter_by(
            sender_id=current_user,
            receiver_id=receiver_id,
            status='pending'
        ).first()

        if existing_request:
            return jsonify({"error": "Request already sent"}), 400

        # Create new request
        new_request = CommunicationRequest(
            sender_id=current_user,
            receiver_id=receiver_id,
            message=message
        )
        db.session.add(new_request)
        db.session.commit()

        # Send WebSocket notification
        socketio.emit('new_communication_request', {
            'request_id': new_request.id,
            'sender_id': current_user,
            'receiver_id': receiver_id,
            'message': message,
            'created_at': new_request.created_at.isoformat()
        }, room=receiver_id)

        return jsonify({
            "message": "Communication request sent",
            "request_id": new_request.id
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/respond-to-request/<int:request_id>", methods=["POST"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def respond_to_communication_request(current_user, request_id):
    try:
        # Fetch incoming request data
        data = request.json
        action = data.get("action")  # 'accept' or 'reject'

        if action not in ['accept', 'reject']:
            return jsonify({"error": "Invalid action"}), 400

        # Get the communication request by its ID
        communication_request = CommunicationRequest.query.get(request_id)
        if not communication_request:
            return jsonify({"error": "Request not found"}), 404

        # Check if the current user is the receiver of this request
        if communication_request.receiver_id == current_user:
            return jsonify({"error": "Unauthorized"}), 403

        # Check if the request is already processed
        if communication_request.status != 'pending':
            return jsonify({"error": "Request already processed"}), 400

        # Update request status based on the action (accept/reject)
        communication_request.status = 'accepted' if action == 'accept' else 'rejected'
        db.session.commit()

        # Notify the sender about the response to the communication request
        socketio.emit('communication_request_response', {
            'request_id': communication_request.id,
            'sender_id': communication_request.sender_id,
            'receiver_id': communication_request.receiver_id,
            'status': communication_request.status,
            'responded_at': datetime.utcnow().isoformat()
        }, room=communication_request.sender_id)

        # If accepted, send a welcome message to the sender
        if action == 'accept':
            welcome_msg = "Hello! I've accepted your communication request."
            socketio.emit('send_message', {
                'sender_id': current_user,
                'receiver_id': communication_request.sender_id,
                'message': welcome_msg
            })

        return jsonify({
            "message": f"Request {action}ed",
            "status": communication_request.status
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_user_full_name(user_id, role):
    if role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=user_id).first()
        if patient:
            return f"{patient.first_name} {patient.last_name}"
    elif role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if doctor:
            return f"{doctor.first_name} {doctor.last_name}"
    return "admin"


@chat.route("/get-pending-requests", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_pending_requests(current_user):
    """Get pending communication requests for current user"""
    try:
        requests = CommunicationRequest.query.filter_by(
            receiver_id=current_user,
            status='pending'
        ).join(User, CommunicationRequest.sender_id == User.id).add_columns(
            CommunicationRequest.id.label('request_id'),
            CommunicationRequest.sender_id,
            CommunicationRequest.message,
            CommunicationRequest.created_at,
            User.email,
            User.role
        ).all()

        request_list = []

        for req in requests:
            sender_id = req.sender_id
            role = req.role.value

            # Get sender name based on role
            sender_name = get_user_full_name(sender_id, role)

            request_list.append({
                "request_id": req.request_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_email": req.email,
                "sender_role": role,
                "message": req.message,
                "created_at": req.created_at.isoformat()
            })

        return jsonify(request_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/get-unread-notification-count", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_unread_notification_count(current_user):
    """Get the count of unread notifications and messages for the current user"""
    try:
        # Count unread messages
        unread_messages_count = Message.query.filter_by(
            receiver_id=current_user,
            read_status=False
        ).count()

        # Count unread notifications
        unread_notifications_count = Notification.query.filter_by(
            user_id=current_user,
            read_status=False
        ).count()

        # Calculate total unread count
        total_unread_count = unread_messages_count + unread_notifications_count

        return jsonify({
            "count": total_unread_count,
            "message_count": unread_messages_count,
            "notification_count": unread_notifications_count,
            "message": "Unread counts retrieved successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to get unread counts"
        }), 500


@chat.route("/get-potential-recipients", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def get_potential_recipients(current_user):
    """Get a list of users that the current user can potentially start a conversation with"""
    try:
        # Get the current user object
        current_user_obj = User.query.get(current_user)
        print(current_user_obj.role)
        if not current_user_obj:
            return jsonify({"error": "User not found"}), 404
        print("1")
        # Fetch users based on role
        if current_user_obj.role == UserRole.ADMIN:
            # Admin can see all users except themselves
            print("2")
            potential_recipients = User.query.filter(User.id != current_user, User.status == True).all()

        elif current_user_obj.role == UserRole.PATIENT:
            # Patient can only see doctors
            doctor_users = db.session.query(User).join(Doctor, Doctor.user_id == User.id) \
                .filter(User.role == 'doctor', User.status == True, User.id != current_user).all()
            potential_recipients = doctor_users

        elif current_user_obj.role == UserRole.DOCTOR:
            # Doctor can see all users except themselves
            potential_recipients = User.query.filter(User.id != current_user, User.status == True).all()

        else:
            # Other roles: empty list
            potential_recipients = []

        # Build the detailed user list
        recipient_list = []
        for user in potential_recipients:
            user_data = {
                "id": user.id,
                "email": user.email,
                "role": str(user.role),
            }
            print(user.role)
            # Add doctor or patient specific details
            if user.role == UserRole.DOCTOR:
                doctor = Doctor.query.filter_by(user_id=user.id).first()
                if doctor:
                    user_data.update({
                        "first_name": doctor.first_name,
                        "last_name": doctor.last_name,
                        "phone": doctor.phone,
                        "qualification": doctor.qualification,
                        "designation": doctor.designation,
                        "bio": doctor.bio,
                        "profile_picture": doctor.profile_picture,
                    })
            elif user.role == UserRole.PATIENT:
                patient = Patient.query.filter_by(user_id=user.id).first()
                if patient:
                    user_data.update({
                        "first_name": patient.first_name,
                        "last_name": patient.last_name,
                        "phone": patient.phone,
                        "age": patient.age,
                        "address": patient.address,
                        "gender": patient.gender,
                    })
            elif user.role == UserRole.DEPARTMENT_HEAD:
                continue

            recipient_list.append(user_data)

        return jsonify(recipient_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/chat", methods=["GET"])
@token_required(
    allowed_roles=[UserRole.DOCTOR.name, UserRole.ADMIN.name, UserRole.PATIENT.name, UserRole.DEPARTMENT_HEAD.name,
                   UserRole.NURSE.name])
def chat_ui(current_user):
    print("Current User ID:", current_user)

    receiver_id = request.args.get('receiver_id')
    receiver_name = None
    receiver_role = None

    if receiver_id:
        receiver = User.query.filter_by(id=receiver_id).first()
        if receiver:
            # Use your helper function to get full name
            receiver_name = get_user_full_name(receiver.id, receiver.role)
            receiver_role = receiver.role.value
        else:
            receiver_name = "Unknown"
            receiver_role = "Unknown"

    return render_template(
        "chat_templates/ch.html",
        current_user=current_user,
        receiver_id=receiver_id,
        receiver_name=receiver_name,
        receiver_role=receiver_role
    )
