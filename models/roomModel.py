from datetime import datetime
from utils.config import db


class Room(db.Model):
    __tablename__ = 'room'

    ROOM_TYPES = {
        '1': ('Standard', 1000.0),
        '2': ('Deluxe', 2000.0),
        '3': ('Suite', 3500.0),
        '4': ('Private', 5000.0),
        '5': ('Ward', 500.0)
    }

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    floor = db.Column(db.String(10), nullable=False)
    room_type = db.Column(db.String(20), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    charge_per_day = db.Column(db.Float, nullable=False)
    is_empty = db.Column(db.Boolean, default=True)  # ✅ This exists
    message = db.Column(db.Text)

    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    department = db.relationship('Department', back_populates='rooms')
    beds = db.relationship('Bed', back_populates='room', cascade='all, delete-orphan')
    charges = db.relationship('RoomCharge', back_populates='room')

    def __init__(self, room_number, floor, room_type, department_id=None, message=None):
        self.room_number = room_number
        self.floor = floor
        self.room_type = room_type
        self.department_id = department_id
        self.message = message
        self.charge_per_day = self.ROOM_TYPES[room_type][1] if room_type in self.ROOM_TYPES else 0


class Bed(db.Model):
    __tablename__ = 'bed'

    id = db.Column(db.Integer, primary_key=True)
    bed_number = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    is_empty = db.Column(db.Boolean, default=True)

    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    room = db.relationship('Room', back_populates='beds')
    allocations = db.relationship('BedAllocation', back_populates='bed', cascade='all, delete-orphan')
    cleanings = db.relationship('BedCleaningLog', back_populates='bed', cascade='all, delete-orphan')
    charges = db.relationship('RoomCharge', back_populates='bed')


class BedAllocation(db.Model):
    __tablename__ = 'bed_allocation'

    STATUS_TYPES = {
        'occupied': 'Occupied',
        'released': 'Released',
        'cancelled': 'Cancelled',
        'other': 'Other',
        'available': 'Available',
        'cleanup': 'Cleanup',
        'reserved': 'Reserved'
    }

    id = db.Column(db.Integer, primary_key=True)
    bed_id = db.Column(db.Integer, db.ForeignKey('bed.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    admission_date = db.Column(db.DateTime, nullable=False)
    discharge_date = db.Column(db.DateTime)
    expected_discharge = db.Column(db.DateTime)
    cleaned_at = db.Column(db.DateTime)  # Timestamp when cleaning is done

    status = db.Column(db.String(20), default='occupied')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bed = db.relationship('Bed', back_populates='allocations')
    patient = db.relationship('Patient', back_populates='allocations')
    cleaning_log = db.relationship('BedCleaningLog', back_populates='allocation', uselist=False)
    charges = db.relationship('RoomCharge', back_populates='allocation', foreign_keys='RoomCharge.allocation_id')


class RoomCharge(db.Model):
    __tablename__ = 'room_charge'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('bed.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    allocation_id = db.Column(db.Integer, db.ForeignKey('bed_allocation.id'))

    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    charge_per_day = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active/completed/cancelled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    room = db.relationship('Room', back_populates='charges')
    bed = db.relationship('Bed', back_populates='charges')
    patient = db.relationship('Patient', back_populates='charges')
    allocation = db.relationship('BedAllocation', back_populates='charges', foreign_keys=[allocation_id])

    def calculate_total(self):
        if self.end_date and self.start_date:
            days = (self.end_date - self.start_date).days or 1
            self.total_amount = days * self.charge_per_day

    @staticmethod
    def create_from_allocation(allocation):
        existing_charge = RoomCharge.query.filter_by(
            bed_id=allocation.bed_id,
            patient_id=allocation.patient_id,
            start_date=allocation.admission_date
        ).first()

        room = allocation.bed.room

        if existing_charge:
            existing_charge.end_date = allocation.discharge_date
            existing_charge.charge_per_day = room.charge_per_day
            existing_charge.calculate_total()
            return existing_charge
        else:
            charge = RoomCharge(
                room_id=room.id,
                bed_id=allocation.bed.id,
                patient_id=allocation.patient_id,
                start_date=allocation.admission_date,
                end_date=allocation.discharge_date,
                charge_per_day=room.charge_per_day
            )
            charge.calculate_total()
            db.session.add(charge)
            return charge


class BedCleaningLog(db.Model):
    __tablename__ = 'bed_cleaning_log'

    id = db.Column(db.Integer, primary_key=True)
    bed_id = db.Column(db.Integer, db.ForeignKey('bed.id'), nullable=False)
    allocation_id = db.Column(db.Integer, db.ForeignKey('bed_allocation.id'))
    cleaned_at = db.Column(db.DateTime,nullable=True)
    cleaned_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # instead of 'user.id'

    remarks = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bed = db.relationship('Bed', back_populates='cleanings')
    allocation = db.relationship('BedAllocation', back_populates='cleaning_log')
    cleaner = db.relationship('User')  # Assuming you have a User model
