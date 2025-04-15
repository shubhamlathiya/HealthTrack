from datetime import datetime, timedelta

from flask import render_template, request, redirect, flash, jsonify
from sqlalchemy import select, or_, and_
from sqlalchemy.util import methods_equivalent

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ROOM_ADD_ROOM, ROOM_AVAILABLE_ROOM, ROOM_BOOK_ROOM, \
    ROOM_ROOM_STATISTICS, \
    ROOM_ROOM_ALLOTTED, ROOM_ROOM_BY_DEPT, ADMIN, ROOM, ROOM_EDIT_ROOM, ROOM_DELETE_ROOM, ROOM_RESTORE_ROOM, \
    GET_PATIENT, ROOM_DISCHARGE_ROOM, ROOM_CLEANING_LOGS, GET_ROOM_DEPARTMENT, ROOM_COMPLETE_CLEANING_LOGS
from middleware.auth_middleware import token_required
from models.departmentModel import Department
from models.patientModel import Patient, PatientPayment
from models.roomModel import Room, Bed, BedAllocation, RoomCharge, BedCleaningLog
from models.userModel import User
from utils.config import db


@admin.route(ROOM, methods=['GET'], endpoint="room")
def list_rooms():
    rooms = Room.query.filter_by(deleted_at=None).order_by(Room.room_number).all()
    departments = Department.query.all()
    deleted_rooms = Room.query.filter_by(is_available=0).order_by(Room.room_number).all()
    return render_template('admin_templates/room/room-list.html', rooms=rooms, departments=departments,
                           deleted_rooms=deleted_rooms)


@admin.route(ROOM_ADD_ROOM, methods=['POST'], endpoint='add-room')
def add_room():
    room_number = request.form.get('room_number')
    floor = request.form.get('floor')
    room_type_key = request.form.get('room_type')
    department_id = request.form.get('department_id')
    message = request.form.get('message')

    # Validate required fields
    if not all([room_number, floor, room_type_key, department_id]):
        flash('All fields except message are required', 'danger')
        return redirect(ADMIN + ROOM_AVAILABLE_ROOM)

    # Check if room number already exists
    if Room.query.filter_by(room_number=room_number).first():
        flash('Room with this number already exists', 'danger')
        return redirect(ADMIN + ROOM_AVAILABLE_ROOM)

    # Get room type name and charge from the ROOM_TYPES dictionary
    room_type_data = Room.ROOM_TYPES.get(room_type_key)
    if not room_type_data:
        flash('Invalid room type selected', 'danger')
        return redirect(ADMIN + ROOM_AVAILABLE_ROOM)

    room_type_name, charge_per_day = room_type_data

    # Create new room
    new_room = Room(
        room_number=room_number,
        floor=floor,
        room_type=room_type_name,
        department_id=int(department_id),
        message=message
    )
    new_room.charge_per_day = charge_per_day  # Redundant but explicit
    new_room.is_available = True

    try:
        db.session.add(new_room)
        db.session.commit()
        flash('Room added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding room: {str(e)}', 'danger')
    return redirect(ADMIN + ROOM)


@admin.route(ROOM_EDIT_ROOM + '/<int:room_id>', methods=['POST'])
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    try:
        # Update basic room information
        room.room_number = request.form.get('room_number')
        room.floor = request.form.get('floor')

        # Handle room type and pricing
        room_type_key = request.form.get('room_type')
        if room_type_key in Room.ROOM_TYPES:
            room.room_type = Room.ROOM_TYPES[room_type_key][0]
            room.charge_per_day = Room.ROOM_TYPES[room_type_key][1]

        # Handle department assignment
        dept_id = request.form.get('department_id')
        room.department_id = int(dept_id) if dept_id else None

        # Handle availability status
        room.is_available = 'is_available' in request.form

        # Update optional message
        room.message = request.form.get('message', '').strip() or None
        db.session.commit()
        flash('Room updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating room: {str(e)}', 'danger')
    return redirect(ADMIN + ROOM)


@admin.route(ROOM_DELETE_ROOM + '/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    try:
        room.is_available = False
        room.deleted_at = datetime.utcnow()
        # Also soft delete all beds in this room
        Bed.query.filter_by(room_id=room_id).update({
            'deleted_at': datetime.utcnow(),
            'is_available': False
        })
        db.session.commit()
        flash('Room and its beds have been archived', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting room: {str(e)}', 'danger')
    return redirect(ADMIN + ROOM)


@admin.route(ROOM_RESTORE_ROOM + '/<int:id>', methods=['POST'])
def room_restore(id):
    room = Room.query.get_or_404(id)
    try:
        # Restore related visits
        room.is_available = True
        room.deleted_at = None
        # Also soft delete all beds in this room
        Bed.query.filter_by(room_id=id).update({
            'deleted_at': None,
            'is_available': True
        })
        db.session.commit()
        flash('Rooms data have been restored!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring Rooms: {str(e)}', 'danger')

    return redirect(ADMIN + ROOM)


@admin.route(ROOM_AVAILABLE_ROOM, methods=['GET'], endpoint='available-room')
def room_available_room():
    # Get all departments with their available rooms and beds
    departments_data = {}

    all_departments = Department.query.filter_by(is_available=1).all()

    print(all_departments)
    for department in all_departments:
        # Get all available rooms for this department
        rooms = Room.query.filter_by(
            department_id=department.id,
            is_available=1,
            is_empty=1
        ).all()
        print(rooms)
        department_rooms = []
        for room in rooms:
            # Get all beds for this room
            beds = Bed.query.filter_by(
                room_id=room.id,
                is_available=1,
                is_empty=1
            ).all()

            for bed in beds:
                department_rooms.append({
                    "room_id": room.id,
                    "bed_id": bed.id,
                    "room_no": room.room_number,
                    "floor": room.floor,
                    "bed_no": bed.bed_number,
                    "room_type": room.room_type,
                    "charge_per_day": room.charge_per_day,
                    "available": room.is_available and room.is_empty and bed.is_available and bed.is_empty
                })

        if department_rooms:  # Only add department if it has available rooms
            departments_data[department.name] = department_rooms

    return render_template("admin_templates/room/available-rooms.html", departments=departments_data)


@admin.route(ROOM_BOOK_ROOM, methods=['POST'], endpoint="book-room")
def book_room():
    # Get form data
    patient_id = request.form.get('patient_id')
    bed_id = request.form.get('bed_id')
    admission_date = datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d')

    try:
        # Create bed allocation
        allocation = BedAllocation(
            bed_id=bed_id,
            patient_id=patient_id,
            admission_date=admission_date,
            status='occupied'
        )

        # Update bed status
        bed = Bed.query.get(bed_id)
        bed.is_empty = False

        # Create room charge
        room_charge = RoomCharge(
            room_id=bed.room_id,
            bed_id=bed_id,
            patient_id=patient_id,
            start_date=admission_date,
            charge_per_day=bed.room.charge_per_day,
            status='active'
        )

        db.session.add(allocation)
        db.session.add(room_charge)
        db.session.commit()

        flash('Room booked successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(ADMIN + ROOM_AVAILABLE_ROOM)


@admin.route(GET_PATIENT + '/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first()  # <-- fixed here

    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    return jsonify({
        'id': patient.id,
        'name': patient.first_name,
        'email': patient.last_name,  # If this is really email, fix the field name
        'phone': patient.phone,
        'gender': patient.gender,
        'age': patient.age
    }), 200


@admin.route(ROOM_ROOM_STATISTICS, methods=['GET'], endpoint='room-statistics')
def room_room_statistics():
    # Fetch bed allocation statistics for the chart (last 12 months)
    current_date = datetime.utcnow()
    monthly_stats = []

    for i in range(12):
        # month_start = current_date.replace(day=1) - timedelta(days=30 * i)
        # month_end = month_start.replace(day=1, month=month_start.month + 1) - timedelta(days=1)
        month_start = (current_date.replace(day=1) - timedelta(days=30 * i)).replace(day=1)

        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1, day=1)

        month_end = next_month - timedelta(days=1)

        stats = {
            'month': month_start.strftime('%b'),
            'occupied': BedAllocation.query.filter(
                BedAllocation.admission_date <= month_end,
                (BedAllocation.discharge_date >= month_start) | (BedAllocation.discharge_date == None),
                BedAllocation.status == 'occupied'
            ).count(),
            'reserved': BedAllocation.query.filter(
                BedAllocation.admission_date <= month_end,
                (BedAllocation.discharge_date >= month_start) | (BedAllocation.discharge_date == None),
                BedAllocation.status == 'reserved'
            ).count(),
            'available': Bed.query.filter(
                ~Bed.allocations.any(
                    (BedAllocation.admission_date <= month_end) &
                    ((BedAllocation.discharge_date >= month_start) | (BedAllocation.discharge_date == None))
                )
            ).count(),
            'cleanup': BedAllocation.query.filter(
                BedAllocation.admission_date <= month_end,
                (BedAllocation.discharge_date >= month_start) | (BedAllocation.discharge_date == None),
                BedAllocation.status == 'cleanup'
            ).count(),
            'other': BedAllocation.query.filter(
                BedAllocation.admission_date <= month_end,
                (BedAllocation.discharge_date >= month_start) | (BedAllocation.discharge_date == None),
                BedAllocation.status == 'other'
            ).count()
        }
        monthly_stats.append(stats)

    # Reverse to show from oldest to newest
    monthly_stats.reverse()

    # Prepare chart data
    chart_data = {
        'categories': [stat['month'] for stat in monthly_stats],
        'series': [
            {'name': 'Occupied', 'data': [stat['occupied'] for stat in monthly_stats]},
            {'name': 'Reserved', 'data': [stat['reserved'] for stat in monthly_stats]},
            {'name': 'Available', 'data': [stat['available'] for stat in monthly_stats]},
            {'name': 'Cleanup', 'data': [stat['cleanup'] for stat in monthly_stats]},
            {'name': 'Other', 'data': [stat['other'] for stat in monthly_stats]}
        ]
    }

    # Fetch current bed allocations for the table
    current_allocations = BedAllocation.query.filter(
        (BedAllocation.discharge_date == None) | (BedAllocation.discharge_date >= datetime.utcnow())
    ).join(Bed).join(Room).join(Department).join(Patient).all()

    # Prepare table data
    table_data = []
    for alloc in current_allocations:
        patient_id = alloc.patient_id
        bed = alloc.bed
        room = bed.room
        department_id = room.department_id

        patient = Patient.query.get_or_404(patient_id)
        department = Department.query.get_or_404(department_id)

        table_data.append({
            'bed_number': bed.bed_number,
            'patient_name': f"{patient.first_name} {patient.last_name}" if patient else "N/A",
            'department': department.name if department else "N/A",
            'admission_date': alloc.admission_date.strftime('%d/%m/%Y') if alloc.admission_date else "N/A",
            'age': patient.age,
            'gender': patient.gender if patient else "N/A",
            'status': alloc.status.capitalize() if alloc.status else "Available",
            'bed_id': bed.id,
            'allocation_id': alloc.id
        })

    # Also include available beds
    available_beds = Bed.query.filter(
        ~Bed.allocations.any(
            (BedAllocation.discharge_date == None) | (BedAllocation.discharge_date >= datetime.utcnow())
        )
    ).join(Room).join(Department).all()

    for bed in available_beds:
        room = bed.room
        department_id = room.department_id
        department = Department.query.get_or_404(department_id)
        table_data.append({
            'bed_number': bed.bed_number,
            'patient_name': "Available",
            'department': department.name if department else "N/A",
            'admission_date': "N/A",
            'age': "N/A",
            'gender': "N/A",
            'status': "Available",
            'bed_id': bed.id,
            'allocation_id': None
        })

    return render_template(
        "admin_templates/room/room-statistics.html",
        chart_data=chart_data,
        table_data=table_data
    )


@admin.route(ROOM_ROOM_ALLOTTED, methods=['GET'], endpoint='rooms-allotted')
def room_rooms_allotted():
    # Get all occupied beds and include cleaning status
    results = db.session.execute(
        select(
            BedAllocation.id.label("allocation_id"),
            BedAllocation.admission_date,
            BedAllocation.discharge_date,
            BedAllocation.expected_discharge,
            BedAllocation.status.label("allocation_status"),
            BedAllocation.cleaned_at,
            Patient.id.label("patient_id"),
            Patient.first_name.label("patient_name"),
            Patient.age,
            Patient.gender,
            Room.id.label("room_id"),
            Room.room_number,
            Room.room_type,
            Room.charge_per_day,
            Bed.bed_number,
            Department.name.label("department_name"),
            BedCleaningLog.id.label("cleaning_log_id"),
            BedCleaningLog.remarks
        )
        .join(Bed, Bed.id == BedAllocation.bed_id)
        .join(Room, Room.id == Bed.room_id)
        .join(Department, Department.id == Room.department_id)
        .join(Patient, Patient.id == BedAllocation.patient_id)
        .outerjoin(BedCleaningLog, BedCleaningLog.allocation_id == BedAllocation.id)
        .where(or_(
            BedAllocation.status == 'occupied',
            and_(
                BedAllocation.status == 'released',
                BedAllocation.cleaned_at == None
            )
        ))
        .order_by(Room.room_number, Bed.bed_number)
    ).fetchall()

    return render_template(
        "admin_templates/room/rooms-allotted.html",
        results=results
    )


@admin.route(ROOM_DISCHARGE_ROOM + "/<int:allocation_id>", methods=["POST"], endpoint="room_discharge")
def discharge_patient(allocation_id):
    try:
        allocation = BedAllocation.query.get_or_404(allocation_id)

        if allocation.status == 'released':
            flash("Patient is already discharged.", "warning")
            return redirect(ADMIN + ROOM_ROOM_ALLOTTED)

        # Set discharge date and update status
        allocation.status = "released"
        allocation.discharge_date = datetime.utcnow()

        # Mark bed as empty but needs cleaning
        bed = Bed.query.get(allocation.bed_id)
        bed.is_empty = True

        # Create cleaning log entry
        cleaning_log = BedCleaningLog(
            bed_id=allocation.bed_id,
            allocation_id=allocation.id,
            remarks="Pending cleaning after discharge",
            cleaned_by=None  # Will be set when cleaning is completed
        )
        db.session.add(cleaning_log)

        # Update or retrieve RoomCharge
        charge = RoomCharge.create_from_allocation(allocation)
        if charge:
            charge.status = "completed"
            db.session.flush()

            if charge.total_amount is None:
                charge.calculate_total()

            payment = PatientPayment(
                patient_id=allocation.patient_id,
                room_charge_id=charge.id,
                amount=charge.total_amount,
                status="unpaid",
                remarks="Room charge upon discharge"
            )
            db.session.add(payment)

        db.session.commit()
        flash("Patient discharged successfully. Bed marked for cleaning.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error during discharge: {str(e)}", "danger")

    return redirect(ADMIN + ROOM_ROOM_ALLOTTED)


@admin.route(ROOM_COMPLETE_CLEANING_LOGS + "/<int:allocation_id>", methods=["GET"], endpoint="complete_cleaning")
@token_required
def complete_cleaning(current_user, allocation_id):
    try:
        allocation = BedAllocation.query.get_or_404(allocation_id)

        if allocation.status != 'released':
            flash("Cannot clean bed for non-discharged patient", "danger")
            return redirect(ADMIN + ROOM_ROOM_ALLOTTED)

        if allocation.cleaned_at:
            flash("Bed already cleaned", "warning")
            return redirect(ADMIN + ROOM_ROOM_ALLOTTED)

        # Update allocation with cleaning time
        allocation.cleaned_at = datetime.utcnow()

        # Update cleaning log
        cleaning_log = BedCleaningLog.query.filter_by(allocation_id=allocation_id).first()
        if cleaning_log:
            cleaning_log.cleaned_at = datetime.utcnow()
            cleaning_log.cleaned_by = current_user  # Assuming you have current_user from Flask-Login
            cleaning_log.remarks = "Cleaning completed"

        # Mark bed as available
        bed = Bed.query.get(allocation.bed_id)
        bed.is_available = True

        db.session.commit()
        flash("Bed cleaning completed and ready for new patients", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error completing cleaning: {str(e)}", "danger")

    return redirect(ADMIN + ROOM_ROOM_ALLOTTED)


@admin.route(ROOM_CLEANING_LOGS, methods=["GET"], endpoint="cleaning_logs")
def cleaning_logs():
    try:
        # Calculate cleaning stats
        total_cleanings = BedCleaningLog.query.count()
        recent_cleanings = BedCleaningLog.query.filter(
            BedCleaningLog.cleaned_at >= datetime.utcnow() - timedelta(days=7)
        ).count()

        stats = {
            'total': total_cleanings,
            'recent': recent_cleanings,
            'completed': BedCleaningLog.query.filter(
                BedCleaningLog.cleaned_at.isnot(None)
            ).count()
        }

        # Get all cleaning logs with related data
        logs = BedCleaningLog.query.options(
            db.joinedload(BedCleaningLog.bed).joinedload(Bed.room),
            db.joinedload(BedCleaningLog.cleaner),
            db.joinedload(BedCleaningLog.allocation)
        ).order_by(BedCleaningLog.cleaned_at.desc()).all()

        return render_template(
            'admin_templates/room/cleaning_logs.html',
            logs=logs,
            stats=stats  # Make sure to pass stats to the template
        )
    except Exception as e:
        return render_template('admin_templates/room/cleaning_logs.html',
                               logs=[],
                               stats={'total': 0, 'recent': 0, 'completed': 0})


@admin.route(ROOM_ROOM_BY_DEPT, methods=['GET'], endpoint='rooms-by-dept')
def room_room_by_dept():
    # Query all non-deleted departments with their rooms
    departments = Department.query.filter_by(deleted_at=None).all()

    dept_data = []
    for dept in departments:
        # Get all non-deleted rooms for this department
        rooms = Room.query.filter_by(department_id=dept.id, deleted_at=None).all()

        # Initialize counters
        stats = {
            'id': dept.id,
            'name': dept.name,
            'total_rooms': len(rooms),
            'total_beds': 0,
            'occupied': 0,
            'reserved': 0,
            'available': 0,
            'needs_cleaning': 0,
            'maintenance': 0,
            'other': 0
        }

        for room in rooms:
            # Get all non-deleted beds for this room
            beds = Bed.query.filter_by(room_id=room.id, deleted_at=None).all()
            stats['total_beds'] += len(beds)

            for bed in beds:
                # Get the latest non-deleted allocation for this bed
                allocation = BedAllocation.query.filter_by(
                    bed_id=bed.id,
                ).order_by(BedAllocation.admission_date.desc()).first()

                if not allocation:
                    if bed.is_available:
                        stats['available'] += 1
                    else:
                        stats['maintenance'] += 1
                else:
                    if allocation.status == 'occupied':
                        stats['occupied'] += 1
                    elif allocation.status == 'reserved':
                        stats['reserved'] += 1
                    elif allocation.status == 'released':
                        if allocation.cleaned_at is None:
                            stats['needs_cleaning'] += 1
                        else:
                            stats['available'] += 1
                    elif allocation.status == 'other':
                        stats['other'] += 1
                    elif allocation.status == 'maintenance':
                        stats['maintenance'] += 1

        # Calculate utilization percentage
        if stats['total_beds'] > 0:
            stats['utilization'] = round(
                (stats['occupied'] / stats['total_beds']) * 100,
                1
            )
        else:
            stats['utilization'] = 0

        dept_data.append(stats)

    # Sort departments by utilization (descending)
    dept_data.sort(key=lambda x: x['utilization'], reverse=True)

    return render_template(
        "admin_templates/room/rooms-by-dept.html",
        departments=dept_data,
        current_time=datetime.utcnow()
    )


@admin.route(GET_ROOM_DEPARTMENT + '/<int:dept_id>')
def get_department_details(dept_id):
    try:
        # Get department basic info
        department = Department.query.get_or_404(dept_id)

        # Get all rooms for this department
        rooms = Room.query.filter_by(department_id=dept_id).all()

        # Prepare response data
        data = {
            'total_rooms': len(rooms),
            'total_beds': 0,
            'available': 0,
            'occupied': 0,
            'reserved': 0,
            'needs_cleaning': 0,
            'maintenance': 0,
            'rooms': []
        }

        # Process each room
        for room in rooms:
            # Get all beds for this room
            beds = Bed.query.filter_by(room_id=room.id).all()
            data['total_beds'] += len(beds)

            for bed in beds:
                # Get current allocation if exists
                allocation = BedAllocation.query.filter_by(
                    bed_id=bed.id,
                    status='occupied'
                ).order_by(BedAllocation.admission_date.desc()).first()

                # Get cleaning status
                needs_cleaning = False
                if allocation and allocation.status == 'released':
                    # Check if it's been cleaned since release
                    last_cleaning = BedCleaningLog.query.filter_by(
                        bed_id=bed.id,
                        allocation_id=allocation.id
                    ).order_by(BedCleaningLog.cleaned_at.desc()).first()

                    if not last_cleaning or last_cleaning.cleaned_at < allocation.discharge_date:
                        needs_cleaning = True

                # Determine status
                if allocation and allocation.status == 'occupied':
                    status = 'occupied'
                    data['occupied'] += 1
                elif allocation and allocation.status == 'reserved':
                    status = 'reserved'
                    data['reserved'] += 1
                elif needs_cleaning:
                    status = 'needs_cleaning'
                    data['needs_cleaning'] += 1
                elif not bed.is_available:
                    status = 'maintenance'
                    data['maintenance'] += 1
                else:
                    status = 'available'
                    data['available'] += 1

                # Get patient info if occupied
                patient_name = None
                admission_date = None
                if allocation and allocation.patient:
                    patient_name = allocation.patient.first_name
                    admission_date = allocation.admission_date.strftime(
                        '%Y-%m-%d') if allocation.admission_date else None

                # Add bed details
                data['rooms'].append({
                    'id': room.id,
                    'room_no': room.room_number,
                    'bed_id': bed.id,
                    'bed_no': bed.bed_number,
                    'status': status,
                    'patient_name': patient_name,
                    'admission_date': admission_date,
                    'allocation_id': allocation.id if allocation else None
                })

        print(data)
        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
