from utils.config import db

class Doctor(db.Model):
    __tablename__ = 'doctor'


    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign Key to User model
    doctor_id = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    qualification = db.Column(db.String(100), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    blood_group = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True)  # Assuming you are storing the image URL

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    department_assignments = db.relationship(
        'DepartmentAssignment',
        back_populates='doctor',
        cascade='all, delete-orphan'
    )

    availabilities = db.relationship(
        'Availability',
        back_populates='doctor',
        cascade='all, delete-orphan'
    )

    appointments = db.relationship('Appointment', foreign_keys='Appointment.doctor_id', back_populates='doctor')
    forwarded_appointments = db.relationship("Appointment", foreign_keys='Appointment.original_doctor_id',
                                             back_populates="original_doctor")

    user = db.relationship('User', back_populates='doctor')
    transfusions = db.relationship('BloodTransfusion', back_populates='doctor')

    def __repr__(self):
        return f"<Doctor {self.first_name} {self.last_name}>"


# Availability model (Each day is a separate record for the doctor)
class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False)  # e.g., 'Sunday', 'Monday'
    from_time = db.Column(db.String(20), nullable=True)  # Start time (e.g., '07:00 AM')
    to_time = db.Column(db.String(20), nullable=True)  # End time (e.g., '05:00 PM')

    # Foreign key to the Doctor model
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    # Relationship
    doctor = db.relationship('Doctor', back_populates='availabilities')

    @property
    def weekly_schedule(self):
        days_map = {
            1: 'Monday', 2: 'Tuesday', 3: 'Wednesday',
            4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'
        }
        schedule = {}
        for availability in self.availabilities:
            day = days_map.get(availability.day_of_week)
            if day:
                schedule[day] = f"{availability.from_time} - {availability.to_time}"
        return schedule

    def __repr__(self):
        return f"<Availability {self.day_of_week} for Doctor {self.doctor_id}>"
