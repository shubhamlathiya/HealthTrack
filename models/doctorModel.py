from utils.config import db

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign Key to User model
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    qualification = db.Column(db.String(100), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    blood_group = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True)  # Assuming you are storing the image URL

    def __repr__(self):
        return f"<Doctor {self.first_name} {self.last_name}>"


# Availability model (Each day is a separate record for the doctor)
class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False)  # e.g., 'Sunday', 'Monday'
    from_time = db.Column(db.String(10), nullable=True)  # Start time (e.g., '9AM')
    to_time = db.Column(db.String(10), nullable=True)  # End time (e.g., '5PM')

    # Foreign key to the Doctor model
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    def __repr__(self):
        return f"<Availability {self.day_of_week} for Doctor {self.doctor_id}>"
