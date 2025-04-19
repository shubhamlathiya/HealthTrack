from datetime import datetime

from utils.config import db


class DeathRecord(db.Model):
    __tablename__ = 'death_records'

    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    birth_date = db.Column(db.Date)
    death_date = db.Column(db.Date, nullable=False)
    death_time = db.Column(db.Time)
    address = db.Column(db.String(200))
    cause_of_death = db.Column(db.String(100), nullable=False)
    guardian_name = db.Column(db.String(100))
    contact_number = db.Column(db.String(20))
    notes = db.Column(db.Text)

    # Doctor relationship
    pronounced_by = db.Column(db.Integer, db.ForeignKey('doctor.id'), index=True)
    doctor = db.relationship('Doctor', backref=db.backref('pronounced_deaths', lazy='dynamic'))

    # Soft delete fields
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<DeathRecord {self.case_number}>'
