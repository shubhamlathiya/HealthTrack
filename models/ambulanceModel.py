from datetime import datetime

from utils.config import db


class Ambulance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_name = db.Column(db.String(100), nullable=False)
    year_made = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)  # Basic, Advanced, Mobile ICU
    base_rate = db.Column(db.Float, nullable=False, default=0.0)
    per_km_rate = db.Column(db.Float, nullable=False, default=0.0)
    is_available = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))

    driver = db.relationship('Driver', backref='ambulances')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)


class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    is_active = db.Column(db.Boolean, default=True)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)


class AmbulanceCall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_age = db.Column(db.Integer, nullable=False)
    patient_gender = db.Column(db.String(10), nullable=False)
    pickup_location = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255))
    call_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    dispatch_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    completion_time = db.Column(db.DateTime)
    distance = db.Column(db.Float)  # in kilometers
    charges = db.Column(db.Float)  # total charges
    status = db.Column(db.String(20), default='Pending')  # Pending, Dispatched, In Progress, Completed, Cancelled
    notes = db.Column(db.Text)

    # Foreign keys
    ambulance_id = db.Column(db.Integer, db.ForeignKey('ambulance.id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))

    # Relationships
    ambulance = db.relationship('Ambulance', backref='calls')
    driver = db.relationship('Driver', backref='calls')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
