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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = db.relationship('Doctor', backref='assignments')
    department = db.relationship('Department')

    def __repr__(self):
        return f'<DepartmentAssignment {self.doctor.full_name} -> {self.department.name}>'