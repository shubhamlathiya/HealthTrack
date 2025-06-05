from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SqlEnum
from utils.config import db
from utils.tokens import generate_verification_token, verify_token


class UserRole(Enum):
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    ACCOUNTANT = 'accountant'
    DEPARTMENT_HEAD = 'department_head'
    PATIENT = 'patient'
    STAFF = 'staff'
    NURSE = 'nurse'
    LABORATORIST = 'laboratorist'
    RECEPTIONIST = 'receptionist'



class User(db.Model):
    __tablename__ = 'users'  # Table name

    # Define columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hash the password during registration
    role = db.Column(SqlEnum(UserRole), nullable=False)
    status = db.Column(db.Boolean, nullable=True)  # Active or inactive
    verified = db.Column(db.Boolean, nullable=True)  # Email verification status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verification_sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    staff = db.relationship('Staff', backref='user', uselist=False)

    notifications = db.relationship('Notification', backref='user', lazy=True)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

    # Relationships
    insurance_records = db.relationship(
        'InsuranceRecord',
        back_populates='patient_user',
        cascade='all, delete-orphan'
    )

    created_claims = db.relationship(
        'InsuranceClaim',
        back_populates='creator',
        cascade='all, delete-orphan'
    )

    patient = db.relationship('Patient', back_populates='user', uselist=False, cascade='all, delete-orphan')
    doctor = db.relationship('Doctor', back_populates='user', uselist=False, cascade='all, delete-orphan')
    requests = db.relationship('BloodRequest', back_populates='requester')
    
    # Constructor to easily create a User object
    def __init__(self, email, password, role, status, verified):
        self.email = email
        self.password = password
        self.role = role if isinstance(role, UserRole) else UserRole(role)
        self.status = status
        self.verified = verified

    def __repr__(self):
        return f'<User {self.email}>'

    def is_department_head(self):
        return self.role == UserRole.DEPARTMENT_HEAD

    def generate_verification_token(self):
        return generate_verification_token(self.id)

    def verify_email(self, token):
        user_id = verify_token(token)
        if user_id == self.id:
            self.verified = True
            db.session.commit()
            return True
        return False