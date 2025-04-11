from utils.config import db


class Ambulance(db.Model):
    __tablename__ = 'ambulance'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False, unique=True)
    vehicle_name = db.Column(db.String(100), nullable=False)
    year_made = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Years available for selection
    YEAR_CHOICES = {
        2020: '2020',
        2021: '2021',
        2022: '2022',
        2023: '2023',
        2024: '2024'
    }

    def __repr__(self):
        return f'<Ambulance {self.vehicle_number}>'