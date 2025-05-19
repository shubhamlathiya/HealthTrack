from datetime import datetime

from utils.config import db


class DepartmentAssignment(db.Model):
    __tablename__ = 'department_assignments'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    specialty = db.Column(db.String(100))
    assigned_date = db.Column(db.Date, default=datetime.utcnow().date)
    experience_level = db.Column(db.Enum('Junior', 'Mid-level', 'Senior', name='experience_level'))
    current_status = db.Column(db.Enum('Active', 'On Leave', 'Inactive', 'Pending', name='assignment_status'))
    notes = db.Column(db.Text)

    # Fixed relationships using back_populates
    doctor = db.relationship('Doctor', back_populates='department_assignments')
    department = db.relationship('Department', back_populates='assignments')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<DepartmentAssignment {self.doctor.first_name} -> {self.department.name}>'