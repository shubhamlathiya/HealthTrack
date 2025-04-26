from werkzeug.security import generate_password_hash, check_password_hash

from utils.config import db


class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    mobile = db.Column(db.String(20))
    designation = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    joining_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Float)
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Suspended
    shift = db.Column(db.String(20))  # Day, Night, Rotational
    experience = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    education = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)
