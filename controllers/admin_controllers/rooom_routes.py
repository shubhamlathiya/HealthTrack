from flask import render_template, request, redirect, flash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ROOM_ADD_ROOM, ROOM_AVAILABLE_ROOM, ROOM_BOOK_ROOM, \
    ROOM_ROOM_STATISTICS, \
    ROOM_ROOM_ALLOTTED, ROOM_ROOM_BY_DEPT
from models.departmentModel import Department
from models.roomModel import Room
from utils.config import db


@admin.route(ROOM_ADD_ROOM, methods=['GET'], endpoint='add-room')
def room_add_room():
    departments = Department.query.all()
    return render_template("admin_templates/room/add-room.html", departments=departments)


@admin.route(ROOM_AVAILABLE_ROOM, methods=['GET'], endpoint='available-room')
def room_available_room():
    return render_template("admin_templates/room/available-rooms.html")


@admin.route(ROOM_BOOK_ROOM, methods=['GET'], endpoint='book-room')
def room_book_room():
    return render_template("admin_templates/room/book-room.html")


@admin.route(ROOM_ROOM_STATISTICS, methods=['GET'], endpoint='room-statistics')
def room_room_statistics():
    return render_template("admin_templates/room/room-statistics.html")


@admin.route(ROOM_ROOM_ALLOTTED, methods=['GET'], endpoint='rooms-allotted')
def room_rooms_allotted():
    return render_template("admin_templates/room/rooms-allotted.html")


@admin.route(ROOM_ROOM_BY_DEPT, methods=['GET'], endpoint='rooms-by-dept')
def room_room_by_dept():
    return render_template("admin_templates/room/rooms-by-dept.html")


@admin.route(ROOM_ADD_ROOM, methods=['POST'])
def add_room():
    room_number = request.form.get('room_number')
    floor = request.form.get('floor')
    room_type = request.form.get('room_type')
    department_id = request.form.get('department_id')
    message = request.form.get('message')

    # Validate required fields
    if not all([room_number, floor, room_type, department_id]):
        flash('All fields except message are required', 'danger')
        return redirect("/admin/" + ROOM_ADD_ROOM)

    # Check if room number already exists
    if Room.query.filter_by(room_number=room_number).first():
        flash('Room with this number already exists', 'danger')
        return redirect("/admin/" + ROOM_ADD_ROOM)

    # Create new room
    new_room = Room(
        room_number=room_number,
        floor=floor,
        room_type=Room.ROOM_TYPES.get(room_type, 'Standard'),
        department_id=department_id,
        message=message,
        is_available=True
    )

    try:
        db.session.add(new_room)
        db.session.commit()
        flash('Room added successfully!', 'success')
        return redirect("/admin/" + ROOM_AVAILABLE_ROOM)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding room: {str(e)}', 'danger')

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
