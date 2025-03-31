from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/room/add-room', methods=['GET'], endpoint='add-room')
def dashboard():
    return render_template("admin_templates/room/add-room.html")


@admin.route('/room/available-room', methods=['GET'], endpoint='available-room')
def dashboard():
    return render_template("admin_templates/room/available-rooms.html")


@admin.route('/room/book-room', methods=['GET'], endpoint='book-room')
def dashboard():
    return render_template("admin_templates/room/book-room.html")


@admin.route('/room/room-statistics', methods=['GET'], endpoint='room-statistics')
def dashboard():
    return render_template("admin_templates/room/room-statistics.html")


@admin.route('/room/rooms-allotted', methods=['GET'], endpoint='rooms-allotted')
def dashboard():
    return render_template("admin_templates/room/rooms-allotted.html")


@admin.route('/room/rooms-by-dept', methods=['GET'], endpoint='rooms-by-dept')
def dashboard():
    return render_template("admin_templates/room/rooms-by-dept.html")

# @admin.route('/add-room', methods=['POST'])
# def add_room():
#     data = request.get_json()
#     room_number = data.get("room_number")
#     room_type = data.get("room_type")
#     status = data.get("status")
#     # current_patient_id = data.get("current_patient_id", None)
#     #
#     # room = Room(room_number, room_type, status, current_patient_id)
#     # room.save()
#     return jsonify({"message": "Room added successfully"}), 201
#
#
# @admin.route('/get-rooms', methods=['GET'])
# def get_rooms():
#     rooms = mongo.db.rooms.find()
#     result = []
#     for room in rooms:
#         result.append({
#             "room_number": room["room_number"],
#             "room_type": room["room_type"],
#             "status": room["status"],
#             "current_patient_id": room["current_patient_id"]
#         })
#     return jsonify(result)
