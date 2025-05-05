from datetime import datetime

from utils.config import db


class Department(db.Model):
    __tablename__ = 'departments'  # Optional: You can specify a custom table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    department_head = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    assignments = db.relationship('DepartmentAssignment', back_populates='department', cascade='all, delete-orphan')
    rooms = db.relationship('Room', back_populates='department')
    staff = db.relationship('Staff', backref='department', lazy=True)
    treatments = db.relationship('Treatment', back_populates='department', cascade='all, delete-orphan')
    lab_reports = db.relationship(
        'LaboratoryTestReport',  # String reference
        back_populates='department',
        lazy='dynamic'
    )
    def __repr__(self):
        return f'<Department {self.name}>'
