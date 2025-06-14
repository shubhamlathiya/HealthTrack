from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SqlEnum

from utils.config import db


class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    emergency_contact = db.Column(db.String(20))
    blood_group = db.Column(db.String(5))
    license_expiry = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)


class Ambulance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_name = db.Column(db.String(100), nullable=False)
    year_made = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)  # Basic, Advanced, Mobile ICU
    base_rate = db.Column(db.Float, nullable=False, default=0.0)
    registration_number = db.Column(db.String(50))
    insurance_number = db.Column(db.String(50))
    insurance_expiry = db.Column(db.Date)
    facilities = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))
    driver = db.relationship('Driver', backref='ambulances')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Ambulance {self.vehicle_number} ({self.vehicle_name})>"


class AmbulanceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        # Corrected repr to reflect AmbulanceCategory
        return f"<AmbulanceCategory {self.name}>"


class AmbulanceChargeItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    standard_charge = db.Column(db.Float, nullable=False, default=0.0)
    # Corrected foreign key and relationship to AmbulanceCategory
    category_id = db.Column(db.Integer, db.ForeignKey('ambulance_category.id'))
    # Corrected relationship and backref name for clarity
    category = db.relationship('AmbulanceCategory', backref='ambulance_charge_items')
    is_active = db.Column(db.Boolean, default=True)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        # Corrected repr to reflect AmbulanceChargeItem
        return f"<AmbulanceChargeItem {self.name} (${self.standard_charge})>"


class AmbulanceCall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    patient = db.relationship('Patient', backref='ambulance_calls')
    patient_name = db.Column(db.String(100), nullable=False)
    patient_age = db.Column(db.Integer, nullable=False)
    patient_gender = db.Column(db.String(10), nullable=False)
    pickup_location = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255))
    # Standardized default for call_time
    call_time = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    dispatch_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    completion_time = db.Column(db.DateTime , nullable=True)
    distance = db.Column(db.Float)  # in kilometers

    # Billing related fields
    base_charge = db.Column(db.Float, default=0.0)
    additional_charges_total = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)
    discount_percent = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    tax_percent = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    payment_mode = db.Column(db.String(50), default='Cash')
    payment_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)

    status = db.Column(db.String(20), default='Pending')  # Pending, Dispatched, In Progress, Completed, Cancelled

    # Foreign keys - Corrected to reference actual model table names
    ambulance_id = db.Column(db.Integer, db.ForeignKey('ambulance.id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))

    # Relationships - Corrected to reference actual model classes and distinct backrefs
    ambulance = db.relationship('Ambulance', backref='calls')
    driver = db.relationship('Driver', backref='calls')
    additional_charge_entries = db.relationship(
        'AdditionalCharge',
        back_populates='call',
        lazy=True,
    )

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<AmbulanceCall {self.call_number} ({self.status})>"


class AdditionalCharge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('ambulance_call.id'))
    # Corrected foreign key and relationship to AmbulanceChargeItem
    charge_item_id = db.Column(db.Integer, db.ForeignKey('ambulance_charge_item.id'))
    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)

    call = db.relationship(
        'AmbulanceCall',
        back_populates='additional_charge_entries',

    )
    charge_item = db.relationship('AmbulanceChargeItem', backref='additional_charge_records')

    # Standardized created_at and updated_at
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        # Corrected repr to reflect AmbulanceChargeItem for name
        return f"<AdditionalCharge {self.charge_item.name} (${self.amount})>"


class AmbulanceRequestStatus(Enum):
    PENDING = 'Pending'
    DISPATCHED = 'Dispatched'
    EN_ROUTE = 'En Route'
    ARRIVED = 'Arrived'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'
    REJECTED = 'Rejected'


class AmbulanceRequest(db.Model):
    __tablename__ = 'ambulance_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    requester_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    request_time = db.Column(db.DateTime, default=datetime.utcnow)
    pickup_location = db.Column(db.String(255), nullable=False)
    emergency_description = db.Column(db.Text, nullable=True)
    status = db.Column(SqlEnum(AmbulanceRequestStatus), nullable=False, default=AmbulanceRequestStatus.PENDING)
    assigned_ambulance_id = db.Column(db.Integer, db.ForeignKey('ambulance.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    requester = db.relationship('User', backref='made_ambulance_requests_as_requester')
    patient = db.relationship('Patient', back_populates='ambulance_requests')
    assigned_ambulance = db.relationship('Ambulance', backref='current_requests')

    def __repr__(self):
        return f'<AmbulanceRequest {self.id} - Status: {self.status.value}>'
