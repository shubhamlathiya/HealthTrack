from datetime import datetime
from enum import Enum

from utils.config import db


class BloodType(Enum):
    A_POSITIVE = 'A+'
    A_NEGATIVE = 'A-'
    B_POSITIVE = 'B+'
    B_NEGATIVE = 'B-'
    AB_POSITIVE = 'AB+'
    AB_NEGATIVE = 'AB-'
    O_POSITIVE = 'O+'
    O_NEGATIVE = 'O-'


class BloodDonor(db.Model):
    __tablename__ = 'blood_donors'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    donation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    blood_type = db.Column(db.Enum(BloodType), nullable=False)
    units_donated = db.Column(db.Float, nullable=False, default=1.0)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Temporary Deferral
    last_donation = db.Column(db.Date)
    next_eligible = db.Column(db.Date)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))

    # Relationships
    patient = db.relationship('Patient', back_populates='donations')
    inventory_items = db.relationship('BloodInventory', back_populates='donor', cascade='all, delete-orphan')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

class BloodInventory(db.Model):
    __tablename__ = 'blood_inventory'

    id = db.Column(db.Integer, primary_key=True)
    blood_type = db.Column(db.Enum(BloodType), nullable=False)
    units_available = db.Column(db.Float, nullable=False, default=0.0)
    donation_id = db.Column(db.Integer, db.ForeignKey('blood_donors.id'), nullable=True)
    expiration_date = db.Column(db.DateTime, nullable=False)
    storage_location = db.Column(db.String(50), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    donor = db.relationship('BloodDonor', back_populates='inventory_items')
    request_items = db.relationship('BloodRequestItem', back_populates='inventory', cascade='all, delete-orphan')
    transfusion_items = db.relationship('BloodTransfusionItem', back_populates='inventory',
                                        cascade='all, delete-orphan')
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)


class BloodRequest(db.Model):
    __tablename__ = 'blood_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    department = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, Approved, Rejected, Completed
    priority = db.Column(db.String(20), nullable=False, default='Normal')  # Low, Normal, High, Emergency
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    requester = db.relationship('User', back_populates='requests')
    patient = db.relationship('Patient', back_populates='blood_requests')
    items = db.relationship('BloodRequestItem', back_populates='request', cascade='all, delete-orphan')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

class BloodRequestItem(db.Model):
    __tablename__ = 'blood_request_items'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('blood_requests.id'), nullable=False)
    blood_type = db.Column(db.Enum(BloodType), nullable=False)
    units_requested = db.Column(db.Float, nullable=False)
    units_approved = db.Column(db.Float, nullable=False, default=0.0)
    inventory_id = db.Column(db.Integer, db.ForeignKey('blood_inventory.id'), nullable=True)

    # Relationships
    request = db.relationship('BloodRequest', back_populates='items')
    inventory = db.relationship('BloodInventory', back_populates='request_items')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

class BloodTransfusion(db.Model):
    __tablename__ = 'blood_transfusions'

    id = db.Column(db.Integer, primary_key=True)
    transfusion_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    notes = db.Column(db.Text, nullable=True)
    adverse_reaction = db.Column(db.Boolean, default=False)
    reaction_details = db.Column(db.Text, nullable=True)

    # Relationships
    patient = db.relationship('Patient', back_populates='blood_transfusions')
    doctor = db.relationship('Doctor', back_populates='transfusions')

    items = db.relationship('BloodTransfusionItem', back_populates='transfusion', cascade='all, delete-orphan')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

class BloodTransfusionItem(db.Model):
    __tablename__ = 'blood_transfusion_items'

    id = db.Column(db.Integer, primary_key=True)
    transfusion_id = db.Column(db.Integer, db.ForeignKey('blood_transfusions.id'), nullable=False)
    blood_type = db.Column(db.Enum(BloodType), nullable=False)
    units_used = db.Column(db.Float, nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('blood_inventory.id'), nullable=False)

    # Relationships
    transfusion = db.relationship('BloodTransfusion', back_populates='items')
    inventory = db.relationship('BloodInventory', back_populates='transfusion_items')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)