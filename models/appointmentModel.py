from datetime import datetime

from utils.config import db


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, canceled, forwarded
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Foreign keys
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    original_doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))  # for forwarded appointments
    original_appointment_id = db.Column(db.Integer, db.ForeignKey(
        'appointments.id'))  # for tracking origin of forwarded/rebooked appointments

    # Relationships
    patient = db.relationship("Patient", back_populates="appointments")
    doctor = db.relationship('Doctor', foreign_keys=[doctor_id], back_populates='appointments')
    original_doctor = db.relationship('Doctor', foreign_keys=[original_doctor_id])
    original_appointment = db.relationship('Appointment', remote_side=[id],
                                           backref=db.backref('derived_appointments',
                                                              remote_side=[original_appointment_id]),
                                           foreign_keys=[original_appointment_id])
    treatments = db.relationship('AppointmentTreatment', back_populates='appointment', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', back_populates='appointment',
                                    cascade='all, delete-orphan')

    # Meta
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)
    canceled_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Appointment {self.id}>'


class AppointmentTreatment(db.Model):
    __tablename__ = 'appointment_treatments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatments.id'), nullable=False)

    price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, completed, canceled

    # Relationships
    appointment = db.relationship('Appointment', back_populates='treatments')
    treatment = db.relationship('Treatment', back_populates='appointment_treatments')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
