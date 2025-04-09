from utils.config import db


class Department(db.Model):
    __tablename__ = 'departments'  # Optional: You can specify a custom table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    department_head = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    number_of_rooms = db.Column(db.Integer, nullable=False)
    number_of_beds = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text)

    def __repr__(self):
        return f'<Department {self.name}>'
