from datetime import datetime

from utils.config import db


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship for coverage types (many-to-many)
    coverages = db.relationship('CoverageType', secondary='provider_coverage', backref='providers')

    def __repr__(self):
        return f'<InsuranceProvider {self.name}>'


class CoverageType(db.Model):
    __tablename__ = 'coverage_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<CoverageType {self.name}>'


# Association table for many-to-many relationship
provider_coverage = db.Table('provider_coverage',
                             db.Column('provider_id', db.Integer, db.ForeignKey('insurance_providers.id'),
                                       primary_key=True),
                             db.Column('coverage_id', db.Integer, db.ForeignKey('coverage_types.id'), primary_key=True)
                             )
