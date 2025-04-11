
from datetime import datetime, timedelta

from utils.config import db


class BloodDonor(db.Model):
    __tablename__ = 'blood_donors'

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.String(10), unique=True, nullable=False)
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
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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