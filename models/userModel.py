from datetime import datetime

from utils.config import db


# Define the User model
class User(db.Model):
    __tablename__ = 'users'  # Table name

    # Define columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hash the password during registration
    role = db.Column(db.String(50), nullable=True)  # Could be 'doctor', 'patient', etc.
    status = db.Column(db.Boolean, nullable=True)  # Active or inactive
    verified = db.Column(db.Boolean, nullable=True)  # Email verification status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    # Constructor to easily create a User object
    def __init__(self, email, password, role, status, verified):
        self.email = email
        self.password = password
        self.role = role
        self.status = status
        self.verified = verified

    def __repr__(self):
        return f'<User {self.email}>'
