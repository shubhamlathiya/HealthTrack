from datetime import datetime

from bson import ObjectId
from flask import jsonify,request

from api.rooms_routes import rooms
from config import mongo


# MongoDB Collections

# 1. Add a Room
@rooms.route('/add-rooms', methods=['POST'])
def add_room():
    data = request.get_json()
    room_number = data.get('room_number')
    room_type = data.get('type')
    notes = data.get('notes', "")

    if not room_number or not room_type:
        return jsonify({"error": "Room number and type are required"}), 400

    room = {
        "room_number": room_number,
        "type": room_type,
        "status": "Available",
        "current_patient_id": None,
        "last_cleaned_at": None,
        "notes": notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    room_id = mongo.db.rooms.insert_one(room).inserted_id
    return jsonify({"message": "Room added successfully", "room_id": str(room_id)}), 201

# 2. Get All Rooms
@rooms.route('/get-rooms', methods=['GET'])
def get_rooms():
    rooms = list(mongo.db.rooms.find())
    for room in rooms:
        room['_id'] = str(room['_id'])
        room['current_patient_id'] = str(room['current_patient_id']) if room['current_patient_id'] else None
    return jsonify({"rooms": rooms}), 200

# 3. Assign a Room to a Patient
@rooms.route('/assign-rooms', methods=['POST'])
def assign_room():
    data = request.get_json()
    room_number = data.get('room_number')
    patient_id = data.get('patient_id')
    notes = data.get('notes', "")

    if not room_number or not patient_id:
        return jsonify({"error": "Room number and patient ID are required"}), 400

    # Check if the room exists and is available
    room = mongo.db.rooms.find_one({"room_number": room_number})
    if not room:
        return jsonify({"error": "Room not found"}), 404
    if room['status'] != "Available":
        return jsonify({"error": "Room is not available"}), 400

    # Update room status and assign patient
    mongo.db.rooms.update_one(
        {"room_number": room_number},
        {
            "$set": {
                "status": "Occupied",
                "current_patient_id": ObjectId(patient_id),
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Add entry to room usage history
    room_usage = {
        "patient_id": ObjectId(patient_id),
        "room_number": room_number,
        "type": room['type'],
        "assigned_at": datetime.utcnow(),
        "released_at": None,
        "notes": notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    mongo.db.room_usage_history.insert_one(room_usage)

    return jsonify({"message": "Room assigned successfully"}), 200

# 4. Release a Room
@rooms.route('/release-rooms', methods=['POST'])
def release_room():
    data = request.get_json()
    room_number = data.get('room_number')

    if not room_number:
        return jsonify({"error": "Room number is required"}), 400

    # Check if the room exists and is occupied
    room = mongo.db.rooms.find_one({"room_number": room_number})
    if not room:
        return jsonify({"error": "Room not found"}), 404
    if room['status'] != "Occupied":
        return jsonify({"error": "Room is not currently occupied"}), 400

    # Update room status to available
    mongo.db.rooms.update_one(
        {"room_number": room_number},
        {
            "$set": {
                "status": "Available",
                "current_patient_id": None,
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Update room usage history
    mongo.db.room_usage_history.update_one(
        {"room_number": room_number, "released_at": None},
        {
            "$set": {
                "released_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )

    return jsonify({"message": "Room released successfully"}), 200

# 5. Get Room Usage History
@rooms.route('/room-usage-history', methods=['GET'])
def get_room_usage_history():
    history = list(mongo.db.room_usage_history.find())
    for entry in history:
        entry['_id'] = str(entry['_id'])
        entry['patient_id'] = str(entry['patient_id'])
    return jsonify({"room_usage_history": history}), 200