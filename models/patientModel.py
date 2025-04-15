from datetime import datetime

from utils.config import db


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign Key to User model
    patient_id = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(10))  # or appropriate type
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='patient', uselist=False)
    allocations = db.relationship('BedAllocation', back_populates='patient')
    charges = db.relationship('RoomCharge', back_populates='patient')

    def __repr__(self):
        return f"<Patient {self.first_name} {self.last_name}>"


class PatientPayment(db.Model):
    __tablename__ = 'patient_payment'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    room_charge_id = db.Column(db.Integer, db.ForeignKey('room_charge.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='unpaid')  # unpaid / paid / pending
    payment_date = db.Column(db.DateTime)
    remarks = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
