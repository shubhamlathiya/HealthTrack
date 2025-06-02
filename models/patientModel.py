from utils.config import db


class Patient(db.Model):
    __tablename__ = 'patient'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign Key to User model
    patient_id = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(10))  # or appropriate type

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', back_populates='patient')
    appointments = db.relationship("Appointment", back_populates="patient")
    allocations = db.relationship('BedAllocation', back_populates='patient', cascade='all, delete-orphan')
    charges = db.relationship('RoomCharge', back_populates='patient', cascade='all, delete-orphan')
    donations = db.relationship("BloodDonor", back_populates="patient")
    blood_requests = db.relationship('BloodRequest', back_populates='patient')
    blood_transfusions = db.relationship("BloodTransfusion", back_populates="patient", cascade="all, delete-orphan")
    # visitors = db.relationship('Visitor', backref='patient', lazy=True)
    def __repr__(self):
        return f"<Patient {self.first_name} {self.last_name}>"


class PatientPayment(db.Model):
    __tablename__ = 'patient_payment'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    room_charge_id = db.Column(db.Integer, db.ForeignKey('room_charge.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='unpaid')  # unpaid / paid / pending
    payment_date = db.Column(db.DateTime)
    remarks = db.Column(db.String(255))

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)
