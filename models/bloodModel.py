from datetime import datetime, timedelta
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from utils.config import db


class BloodDonor(db.Model):
    __tablename__ = 'blood_donors'

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.String(10), unique=True, nullable=False)
    patient_id = db.Column(db.String(20), nullable=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Temporary Deferral
    last_donation = db.Column(db.Date)
    next_eligible = db.Column(db.Date)
    registration_date = db.Column(db.Date, default=datetime.utcnow)
    medical_history = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    notes = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    donations = relationship('BloodProduct', back_populates='donor', lazy='dynamic')

    BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

    def __init__(self, **kwargs):
        super(BloodDonor, self).__init__(**kwargs)
        if not self.donor_id:
            self.generate_donor_id()

    def generate_donor_id(self):
        last_donor = BloodDonor.query.order_by(BloodDonor.id.desc()).first()
        last_id = int(last_donor.donor_id[1:]) if last_donor else 0
        self.donor_id = f"D{last_id + 1:03d}"

    def calculate_next_eligible(self):
        if self.last_donation:
            self.next_eligible = self.last_donation + timedelta(days=90)  # 3 months deferral period

    def __repr__(self):
        return f'<BloodDonor {self.donor_id} - {self.first_name} {self.last_name}>'

    def calculate_age(self):
        """Calculate age based on date_of_birth"""
        if not self.date_of_birth:
            return None
        today = datetime.utcnow().date()
        return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class BloodProduct(db.Model):
    __tablename__ = 'blood_stock'

    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(20), unique=True, nullable=False)
    donor_id = db.Column(db.String(10), ForeignKey('blood_donors.donor_id'), nullable=True)
    blood_type = db.Column(db.String(5), nullable=False)  # A+, A-, B+, etc.
    component_type = db.Column(db.String(50), nullable=False)  # Whole Blood, RBC, Plasma, etc.
    status = db.Column(db.String(20))
    quantity = db.Column(db.Integer, nullable=False)  # in units
    collection_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    storage_location = db.Column(db.String(100), nullable=False)
    batch_number = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    donor = relationship('BloodDonor', back_populates='donations')
    issuances = relationship('BloodIssuance', back_populates='blood_product', lazy='dynamic')

    def update_status(self):
        """Method to update the status field"""
        self.status = self._calculate_status()
        return self.status

    def _calculate_status(self):
        """Internal method for status calculation"""
        today = datetime.now().date()
        days_remaining = (self.expiry_date - today).days
        if days_remaining <= 0:
            return 'Expired'
        elif days_remaining <= 7:
            return 'Near Expiry'
        return 'Fresh'

    def __repr__(self):
        return f'<BloodProduct {self.product_code} - {self.blood_type} {self.component_type}>'


class BloodIssuance(db.Model):
    __tablename__ = 'blood_issuances'

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.String(20), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_age = db.Column(db.Integer)
    patient_gender = db.Column(db.String(10))
    blood_product_id = db.Column(db.Integer, ForeignKey('blood_stock.id'), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    component_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.String(20), nullable=False)  # e.g., "350 mL" or "1 Unit"
    issue_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Transfused, Cancelled
    doctor_id = db.Column(db.String(20))
    transfusion_date = db.Column(db.Date)
    issue_reason = db.Column(db.String(200))
    remarks = db.Column(db.Text)
    issued_by = db.Column(db.String(100))
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    blood_product = relationship('BloodProduct', back_populates='issuances')

    def generate_issue_id(self):
        last_issue = BloodIssuance.query.order_by(BloodIssuance.id.desc()).first()
        last_num = int(last_issue.issue_id[2:]) if last_issue else 0
        self.issue_id = f"BI{last_num + 1:03d}"

    def __repr__(self):
        return f'<BloodIssuance {self.issue_id} - {self.patient_name}>'


# class DonationHistory(db.Model):
#     __tablename__ = 'donation_history'
#
#     id = db.Column(db.Integer, primary_key=True)
#     donation_id = db.Column(db.String(20), unique=True, nullable=False)
#     donor_id = db.Column(db.String(10), ForeignKey('blood_donors.donor_id'), nullable=False)
#     donation_date = db.Column(db.Date, nullable=False)
#     blood_type = db.Column(db.String(5), nullable=False)
#     volume = db.Column(db.Integer, nullable=False)  # in mL
#     hemoglobin_level = db.Column(db.Float)
#     blood_pressure = db.Column(db.String(20))
#     pulse_rate = db.Column(db.Integer)
#     donation_type = db.Column(db.String(50))  # Whole blood, plasma, platelets, etc.
#     notes = db.Column(db.Text)
#     is_deleted = db.Column(db.Boolean, default=False)
#     created_at = db.Column(db.DateTime, default=datetime.now)
#     updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
#
#     # Relationships
#     donor = relationship('BloodDonor', back_populates='donations_history')
#
#     def generate_donation_id(self):
#         last_donation = DonationHistory.query.order_by(DonationHistory.id.desc()).first()
#         last_num = int(last_donation.donation_id[2:]) if last_donation else 0
#         self.donation_id = f"DH{last_num + 1:03d}"
#
#     def __repr__(self):
#         return f'<DonationHistory {self.donation_id} - Donor: {self.donor_id}>'
