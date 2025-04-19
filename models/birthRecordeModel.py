from datetime import datetime

from utils.config import db


class ChildCase(db.Model):
    __tablename__ = 'child_cases'

    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    mother_name = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Active')
    case_notes = db.Column(db.Text)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    medical_visits = db.relationship('MedicalVisit', backref='child_case', lazy=True)


class MedicalVisit(db.Model):
    __tablename__ = 'medical_visits'

    id = db.Column(db.Integer, primary_key=True)
    child_case_id = db.Column(db.Integer, db.ForeignKey('child_cases.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    visit_type = db.Column(db.String(50), nullable=False)
    height = db.Column(db.String(10))
    weight = db.Column(db.String(10))
    notes = db.Column(db.Text)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))

    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    doctor = db.relationship('Doctor', backref='medical_visits')
