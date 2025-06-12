from utils.config import db


class Department(db.Model):
    __tablename__ = 'departments'  # Optional: You can specify a custom table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    message = db.Column(db.Text)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    assignments = db.relationship('DepartmentAssignment', back_populates='department', cascade='all, delete-orphan')
    rooms = db.relationship('Room', back_populates='department')
    staff = db.relationship('Staff', backref='department', lazy=True)
    treatments = db.relationship('Treatment', back_populates='department', cascade='all, delete-orphan')
    lab_reports = db.relationship(
        'LaboratoryTestReport',  # String reference
        back_populates='department',
        lazy='dynamic'
    )
    heads = db.relationship('DepartmentHead', back_populates='department', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Department {self.name}>'


class DepartmentHead(db.Model):
    __tablename__ = 'department_heads'
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    start_date = db.Column(db.DateTime, server_default=db.func.now())
    end_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    department = db.relationship('Department', back_populates='heads')
    doctor = db.relationship('Doctor', backref='head_positions')  # Fixed typo here

    def __repr__(self):
        return f'<DepartmentHead {self.doctor_id} for Department {self.department_id}>'
