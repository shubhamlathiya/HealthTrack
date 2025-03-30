from flask import jsonify,request

from controllers.admin_controllers import admin
from utils.config import mongo


@admin.route('/add-room', methods=['POST'])
def add_room():
    data = request.get_json()
    room_number = data.get("room_number")
    room_type = data.get("room_type")
    status = data.get("status")
    # current_patient_id = data.get("current_patient_id", None)
    #
    # room = Room(room_number, room_type, status, current_patient_id)
    # room.save()
    return jsonify({"message": "Room added successfully"}), 201

@admin.route('/get-rooms', methods=['GET'])
def get_rooms():
    rooms = mongo.db.rooms.find()
    result = []
    for room in rooms:
        result.append({
            "room_number": room["room_number"],
            "room_type": room["room_type"],
            "status": room["status"],
            "current_patient_id": room["current_patient_id"]
        })
    return jsonify(result)
