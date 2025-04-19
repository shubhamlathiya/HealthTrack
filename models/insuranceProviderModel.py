from datetime import datetime
from utils.config import db

# Association table for many-to-many relationship between providers and coverage types
provider_coverage = db.Table('provider_coverage',
    db.Column('provider_id', db.Integer, db.ForeignKey('insurance_providers.id'), primary_key=True),
    db.Column('coverage_id', db.Integer, db.ForeignKey('coverage_types.id'), primary_key=True)
)


class InsuranceProvider(db.Model):
    __tablename__ = 'insurance_providers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    website = db.Column(db.String(100))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    support_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    contract_start = db.Column(db.Date, nullable=False)
    contract_end = db.Column(db.Date, nullable=False)
    reimbursement_rate = db.Column(db.Float, nullable=False)
    payment_terms = db.Column(db.String(100))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Renewal Pending

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    coverages = db.relationship('CoverageType', secondary=provider_coverage, backref='providers')
    insurance_records = db.relationship(
        'InsuranceRecord', back_populates='insurance_provider', lazy=True,
        cascade='all, delete-orphan'
    )
    claims = db.relationship(
        'InsuranceClaim', back_populates='insurance_provider', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<InsuranceProvider {self.name}>'

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'website': self.website,
            'phone': self.phone,
            'email': self.email,
            'status': self.status,
            'contract_start': self.contract_start.strftime('%Y-%m-%d') if self.contract_start else None,
            'contract_end': self.contract_end.strftime('%Y-%m-%d') if self.contract_end else None,
            'coverages': [coverage.name for coverage in self.coverages]
        }


class CoverageType(db.Model):
    __tablename__ = 'coverage_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<CoverageType {self.name}>'

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }


class InsuranceRecord(db.Model):
    __tablename__ = 'insurance_records'

    id = db.Column(db.Integer, primary_key=True)
    insurance_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.String(20), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    policy_number = db.Column(db.String(50), nullable=False)
    policy_type = db.Column(db.String(20), nullable=False)  # Individual, Family, Corporate, Group
    coverage_start = db.Column(db.Date, nullable=False)
    coverage_end = db.Column(db.Date, nullable=False)
    coverage_amount = db.Column(db.Numeric(12, 2), nullable=False)
    copayment = db.Column(db.Numeric(5, 2), default=0)
    status = db.Column(db.String(20), nullable=False)  # Active, Pending, Expired
    remarks = db.Column(db.Text)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Foreign Keys
    insurance_provider_id = db.Column(db.Integer, db.ForeignKey('insurance_providers.id'))
    patient_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    insurance_provider = db.relationship(
        'InsuranceProvider', back_populates='insurance_records'
    )
    patient_user = db.relationship(
        'User', back_populates='insurance_records'
    )
    claims = db.relationship(
        'InsuranceClaim', back_populates='insurance_record', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<InsuranceRecord {self.insurance_id} for {self.patient_name}>'

    def serialize(self):
        return {
            'id': self.id,
            'insurance_id': self.insurance_id,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'policy_number': self.policy_number,
            'policy_type': self.policy_type,
            'coverage_start': self.coverage_start.strftime('%Y-%m-%d'),
            'coverage_end': self.coverage_end.strftime('%Y-%m-%d'),
            'coverage_amount': float(self.coverage_amount),
            'copayment': float(self.copayment),
            'status': self.status,
            'remarks': self.remarks,
            'provider': self.insurance_provider.serialize() if self.insurance_provider else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class InsuranceClaim(db.Model):
    __tablename__ = 'insurance_claims'

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.String(20), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    claim_date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    diagnosis_code = db.Column(db.String(20), nullable=False)  # ICD-10
    procedure_code = db.Column(db.String(20), nullable=False)  # CPT
    service_description = db.Column(db.Text, nullable=False)
    claim_amount = db.Column(db.Numeric(12, 2), nullable=False)
    approved_amount = db.Column(db.Numeric(12, 2))
    deductible = db.Column(db.Numeric(10, 2), default=0)
    copayment = db.Column(db.Numeric(10, 2), default=0)
    patient_responsibility = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected
    remarks = db.Column(db.Text)

    # Foreign key to User who created the claim
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship back to User
    creator = db.relationship('User', back_populates='created_claims')


    # Foreign Keys
    insurance_provider_id = db.Column(db.Integer, db.ForeignKey('insurance_providers.id'))
    insurance_record_id = db.Column(db.Integer, db.ForeignKey('insurance_records.id'))

    # Relationships
    insurance_provider = db.relationship('InsuranceProvider', back_populates='claims')
    insurance_record = db.relationship('InsuranceRecord', back_populates='claims')

    def __repr__(self):
        return f'<InsuranceClaim {self.claim_id}>'