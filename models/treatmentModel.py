from utils.config import db


class Treatment(db.Model):
    __tablename__ = 'treatments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=30)  # Default appointment duration
    base_price = db.Column(db.Float, nullable=False)
    icon = db.Column(db.String(50), default='emergency')  # Matches icon filenames
    active = db.Column(db.Boolean, default=True)

    # Foreign key to department
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)

    # Relationships
    department = db.relationship('Department', back_populates='treatments')
    appointment_treatments = db.relationship('AppointmentTreatment', back_populates='treatment')

    # Status tracking
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Treatment {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration': self.duration_minutes,
            'price': self.base_price,
            'icon': self.icon,
            'department': self.department.name if self.department else None,
            'department_id': self.department_id
        }
