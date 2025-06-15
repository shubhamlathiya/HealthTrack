from datetime import datetime

from utils.config import db


class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)

    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='Issued')  # Issued, Filled, Canceled

    # Meta
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    appointment = db.relationship('Appointment', back_populates='prescriptions')
    medications = db.relationship('PrescriptionMedication', back_populates='prescription', cascade='all, delete-orphan')
    test_reports = db.relationship('PrescriptionTestReport', back_populates='prescription',
                                   cascade='all, delete-orphan')


class PrescriptionMedication(db.Model):
    __tablename__ = 'prescription_medications'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    meal_instructions = db.Column(db.String(50), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    prescription = db.relationship('Prescription', back_populates='medications')
    timings = db.relationship('MedicationTiming', back_populates='medication', cascade='all, delete-orphan')


class MedicationTiming(db.Model):
    __tablename__ = 'medication_timings'

    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('prescription_medications.id'), nullable=False)
    timing = db.Column(db.String(20), nullable=False)  # Morning, Afternoon, Evening, Night

    medication = db.relationship('PrescriptionMedication', back_populates='timings')


class PrescriptionTestReport(db.Model):
    __tablename__ = 'prescription_test_reports'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    lab_report_id = db.Column(db.Integer, db.ForeignKey('laboratory_test_reports.id'), nullable=True)

    report_name = db.Column(db.String(255), nullable=False)
    report_notes = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Completed
    file_path = db.Column(db.String(255))  # Path to uploaded report

    prescription = db.relationship('Prescription', back_populates='test_reports')
    lab_report = db.relationship(
        'LaboratoryTestReport',
        back_populates='prescription_reports'
    )