from flask import jsonify,request

from api.rooms_routes import rooms
from config import mongo


@rooms.route('/add-room-activity', methods=['POST'])
def add_room_activity():
    data = request.get_json()
    room_number = data.get("room_number")
    activity_type = data.get("activity_type")  # Either "cleaning" or "maintenance"

    # Validation
    if not all([room_number, activity_type]):
        return jsonify({"error": "Room number and activity type are required"}), 400

    room = mongo.db.room_activities.find_one({"room_number": room_number})
    if not room:
        room = {
            "room_number": room_number,
            "activities": []
        }

    if activity_type == "cleaning":
        cleaning_schedule = data.get("schedule")
        if not all([cleaning_schedule.get("date"), cleaning_schedule.get("cleaning_assigned_to")]):
            return jsonify({"error": "Cleaning date and assigned staff are required"}), 400

        activity = {
            "type": "cleaning",
            "schedule": cleaning_schedule
        }

    elif activity_type == "maintenance":
        maintenance_request = data.get("request")
        if not all([maintenance_request.get("issue_description"), maintenance_request.get("assigned_to")]):
            return jsonify({"error": "Maintenance issue description and assigned technician are required"}), 400

        activity = {
            "type": "maintenance",
            "request": maintenance_request
        }

    else:
        return jsonify({"error": "Invalid activity type"}), 400

    # Add activity to the room document
    room["activities"].append(activity)
    mongo.db.room_activities.update_one({"room_number": room_number}, {"$set": room}, upsert=True)

    return jsonify({"message": f"{activity_type.capitalize()} activity added successfully"}), 201


@rooms.route('/get-room-activities/<room_number>', methods=['GET'])
def get_room_activities(room_number):
    room = mongo.db.room_activities.find_one({"room_number": room_number})
    if not room:
        return jsonify({"error": "Room not found"}), 404

    return jsonify({"activities": room["activities"]}), 200


@rooms.route('/update-cleaning-status', methods=['POST'])
def update_cleaning_status():
    data = request.get_json()
    room_number = data.get("room_number")
    cleaning_date = data.get("cleaning_date")
    completed_by = data.get("completed_by")

    # Find the room and update the cleaning schedule
    room = mongo.db.room_activities.find_one({"room_number": room_number})
    if not room:
        return jsonify({"error": "Room not found"}), 404

    for activity in room["activities"]:
        if activity["type"] == "cleaning" and activity["schedule"]["date"] == datetime.datetime.strptime(cleaning_date, "%Y-%m-%dT%H:%M:%SZ"):
            activity["schedule"]["cleaning_status"] = "Completed"
            activity["schedule"]["completed_by"] = completed_by
            mongo.db.room_activities.update_one({"room_number": room_number}, {"$set": room})
            return jsonify({"message": "Cleaning status updated successfully"}), 200

    return jsonify({"error": "Cleaning activity not found"}), 404
