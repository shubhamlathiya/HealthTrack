from datetime import datetime

from utils.config import db


class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20), nullable=False)
    check_in = db.Column(db.DateTime, default=datetime.now)
    check_out = db.Column(db.DateTime)
    qr_code = db.Column(db.String(100))  # Stores QR code filename
    is_active = db.Column(db.Boolean, default=True)

class VisitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitor.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    check_in = db.Column(db.DateTime, default=datetime.now)
    check_out = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)  # For real-time tracking