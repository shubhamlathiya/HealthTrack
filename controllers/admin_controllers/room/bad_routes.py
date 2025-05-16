from datetime import datetime

from flask import request, flash, redirect, render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ROOM_ADD_BAD, ADMIN, ROOM_DELETE_BAD, ROOM
from middleware.auth_middleware import token_required
from models.roomModel import Room, Bed
from models.userModel import UserRole
from utils.config import db


@admin.route(ROOM_ADD_BAD + '/<int:room_id>', methods=['GET', 'POST'], endpoint='add_bed')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_bed(current_user , room_id):
    # Get the room or return 404 if not found
    room = Room.query.get_or_404(int(room_id))

    # Calculate next available bed number
    last_bed = Bed.query.filter_by(room_id=room.id) \
        .order_by(Bed.bed_number.desc()) \
        .first()
    next_bed_number = last_bed.bed_number + 1 if last_bed else 1

    if request.method == 'POST':
        try:
            # Create new bed
            new_bed = Bed(
                bed_number=next_bed_number,
                room_id=room_id,
                is_empty=True,
                is_deleted=False
            )

            db.session.add(new_bed)
            db.session.commit()

            flash(f'Bed {next_bed_number} added successfully to Room {room.room_number}', 'success')
            return redirect(ADMIN + ROOM_ADD_BAD + "/" + str(room.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add bed: {str(e)}', 'danger')

    return render_template('admin_templates/room/add_bed.html',
                           room=room,
                           next_bed_number=next_bed_number,
                           ADMIN = ADMIN,
                           ROOM = ROOM)


@admin.route(ROOM_DELETE_BAD + '/<int:bed_id>', methods=['POST'], endpoint='delete_bed')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_bed(current_user ,bed_id):
    bed = Bed.query.get_or_404(bed_id)
    try:
        bed.is_deleted = True
        bed.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Bed has been archived', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting bed: {str(e)}', 'danger')

    return redirect(ADMIN + ROOM_ADD_BAD + str(bed.room_id))
