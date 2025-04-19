from datetime import datetime

from utils.config import db


class MedicineCategory(db.Model):
    __tablename__ = 'medicine_categories'

    id = db.Column(db.Integer, primary_key=True ,autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    medicines = db.relationship('Medicine', backref='category', lazy=True)

    def __repr__(self):
        return f'<MedicineCategory {self.name}>'


class MedicineCompany(db.Model):
    __tablename__ = 'medicine_companies'

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.Text)
    contact_number = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website = db.Column(db.String(255))

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    medicines = db.relationship('Medicine', backref='company', lazy=True)

    def __repr__(self):
        return f'<MedicineCompany {self.name}>'


class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True ,autoincrement=True)
    medicine_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('medicine_categories.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('medicine_companies.id'))
    purchase_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    current_stock = db.Column(db.Integer, default=0, nullable=False)
    min_stock_level = db.Column(db.Integer, default=10, nullable=False)
    location = db.Column(db.String(50))
    barcode = db.Column(db.String(50), unique=True)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    stock_transactions = db.relationship('StockTransaction', backref='medicine', lazy=True)

    @property
    def status(self):
        if self.current_stock <= 0:
            return 'Out of Stock'
        elif self.current_stock <= self.min_stock_level:
            return 'Low Stock'
        elif self.expiry_date < datetime.now().date():
            return 'Expired'
        else:
            return 'In Stock'

    @property
    def status_badge(self):
        status = self.status
        if status == 'Out of Stock':
            return 'danger'
        elif status == 'Low Stock':
            return 'warning'
        elif status == 'Expired':
            return 'dark'
        else:
            return 'success'

    def __repr__(self):
        return f'<Medicine {self.name} ({self.medicine_number})>'


class StockTransaction(db.Model):
    __tablename__ = 'stock_transactions'

    id = db.Column(db.Integer, primary_key=True ,autoincrement=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # purchase, dispense, adjustment, etc.
    quantity = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(100))  # prescription ID, purchase order, etc.
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='stock_transactions')

    def __repr__(self):
        return f'<StockTransaction {self.transaction_type} {self.quantity} units of {self.medicine.name}>'
