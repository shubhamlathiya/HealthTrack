from utils.config import db


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), nullable=False, unique=True)
    floor = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    message = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    ROOM_TYPES = {
        '1': 'Standard',
        '2': 'Deluxe',
        '3': 'Suite',
        '4': 'Private',
        '5': 'Ward'
    }

    def __repr__(self):
        return f'<Room {self.room_number}>'
