from datetime import datetime, date, timedelta  # Import date and timedelta specifically
from enum import Enum

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Numeric

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


class MedicineGroup(db.Model):
    __tablename__ = 'medicine_groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    medicines = db.relationship('Medicine', backref='group', lazy=True)

    def __repr__(self):
        return f'<MedicineGroup {self.name}>'


class MedicineUnit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    symbol = db.Column(db.String(10), nullable=False)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    medicines = db.relationship('Medicine', backref='unit', lazy=True)

    def __repr__(self):
        return f'<Unit {self.name} ({self.symbol})>'


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    tax_id = db.Column(db.String(50))
    payment_terms = db.Column(db.Text)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    purchases = db.relationship('MedicinePurchase', backref='supplier', lazy=True)

    def __repr__(self):
        return f'<Supplier {self.name}>'


class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medicine_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    composition = db.Column(db.Text)

    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey('medicine_categories.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('medicine_companies.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('medicine_groups.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))

    # Inventory fields
    min_level = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)
    box_packing = db.Column(db.Integer, default=1)
    rack_number = db.Column(db.String(20))
    default_tax_rate = db.Column(Numeric(5, 2), default=0.00)
    vat_account = db.Column(db.String(50))

    # Pricing fields (defaults)
    default_purchase_price = db.Column(Numeric(10, 2), default=0.00)
    default_selling_price = db.Column(Numeric(10, 2), default=0.00)
    default_mrp = db.Column(Numeric(10, 2), default=0.00)
    barcode = db.Column(db.String(100), unique=True)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    batches = db.relationship('MedicineBatch', backref='medicine', lazy=True)
    purchase_items = db.relationship('PurchaseItem', backref='medicine', lazy=True)
    stock_transactions = db.relationship('StockTransaction', back_populates='medicine')
    requested_items = db.relationship('MedicineRequestItem', back_populates='medicine', lazy=True)

    @property
    def current_stock(self):
        return sum(batch.current_stock for batch in self.batches if not batch.is_deleted)

    @property
    def status(self):
        if self.current_stock <= 0:
            return 'Out of Stock'
        elif self.current_stock <= self.reorder_level:
            return 'Low Stock'
        else:
            return 'In Stock'

    def __repr__(self):
        return f'<Medicine {self.name} ({self.medicine_number})>'


class MedicinePurchase(db.Model):
    __tablename__ = 'medicine_purchases'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_no = db.Column(db.String(20), unique=True, nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)

    # Financial fields
    subtotal = db.Column(Numeric(10, 2), default=0.00)
    discount_percent = db.Column(Numeric(5, 2), default=0.00)
    discount_amount = db.Column(Numeric(10, 2), default=0.00)
    tax_amount = db.Column(Numeric(10, 2), default=0.00)
    total_amount = db.Column(Numeric(10, 2), default=0.00)
    paid_amount = db.Column(Numeric(10, 2), default=0.00)
    due_amount = db.Column(Numeric(10, 2), default=0.00)

    # Payment info
    payment_mode = db.Column(db.String(20), default='Cash')
    payment_note = db.Column(db.Text)

    # Additional info
    note = db.Column(db.Text)
    attachment = db.Column(db.String(255))  # File path for uploaded document

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True)

    def __repr__(self):
        return f'<MedicinePurchase {self.bill_no}>'


class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('medicine_purchases.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)

    # Batch info
    batch_no = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)

    # Quantity info
    packing_qty = db.Column(db.Integer, default=1)
    quantity = db.Column(db.Integer, nullable=False)

    # Pricing
    mrp = db.Column(Numeric(10, 2), nullable=False)
    purchase_price = db.Column(Numeric(10, 2), nullable=False)
    sale_price = db.Column(Numeric(10, 2), nullable=False)
    tax_rate = db.Column(Numeric(5, 2), default=0.00)
    tax_amount = db.Column(Numeric(10, 2), default=0.00)
    amount = db.Column(Numeric(10, 2), nullable=False)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    batch = db.relationship('MedicineBatch', backref='purchase_item', uselist=False)

    def __repr__(self):
        return f'<PurchaseItem {self.medicine.name} x {self.quantity}>'


class MedicineBatch(db.Model):
    __tablename__ = 'medicine_batches'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    purchase_item_id = db.Column(db.Integer, db.ForeignKey('purchase_items.id'))

    # Batch info
    batch_no = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)

    # Pricing
    purchase_price = db.Column(Numeric(10, 2), nullable=False)
    selling_price = db.Column(Numeric(10, 2), nullable=False)
    mrp = db.Column(Numeric(10, 2), nullable=False)
    tax_rate = db.Column(Numeric(5, 2), default=0.00)

    # Stock info
    initial_quantity = db.Column(db.Integer, nullable=False)
    current_stock = db.Column(db.Integer, nullable=False, default=0)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    stock_transactions = db.relationship('StockTransaction', back_populates='batch')

    @property
    def status(self):
        if self.current_stock <= 0:
            return 'Out of Stock'
        elif self.expiry_date < datetime.now().date():
            return 'Expired'
        else:
            return 'Available'

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date <= date.today()  # Corrected: Call date.today() with parentheses
        return False

    @property
    def is_near_expiry(self):
        if self.expiry_date:
            return date.today() < self.expiry_date <= date.today() + timedelta(
                days=90)  # Corrected: Call date.today() and timedelta() with parentheses
        return False

    def __repr__(self):
        return f'<MedicineBatch {self.batch_no} of {self.medicine.name}>'


class StockTransaction(db.Model):
    __tablename__ = 'stock_transactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # ✅ Add this line
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # purchase, sale, adjustment, etc.
    quantity = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(100))  # Can reference bills, purchases, etc.
    notes = db.Column(db.Text)

    medicine = db.relationship('Medicine', back_populates='stock_transactions')

    batch = db.relationship('MedicineBatch', back_populates='stock_transactions')

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    def __repr__(self):
        return f'<StockTransaction {self.transaction_type} of {self.quantity} units>'


class  MedicineSale(db.Model):
    __tablename__ = 'medicine_sales'

    id = db.Column(db.Integer, primary_key=True)
    prescription_no = db.Column(db.String(50), unique=True, nullable=True)
    patient_id = db.Column(db.Integer, nullable=False)
    bill_no = db.Column(db.String(50), unique=True, nullable=False)
    case_id = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)
    note = db.Column(db.Text)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.00)
    net_amount = db.Column(db.Numeric(10, 2), default=0.00)
    payment_mode = db.Column(db.String(20), default='Cash')
    payment_amount = db.Column(db.Numeric(10, 2), default=0.00)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    items = db.relationship('MedicineSaleItem', backref='sale', lazy=True)
    doctor = db.relationship('Doctor', backref='prescriptions')

    def __repr__(self):
        return f'<MedicineSale {self.prescription_no}>'


class MedicineSaleItem(db.Model):
    __tablename__ = 'medicine_sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('medicine_sales.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    medicine = db.relationship('Medicine', backref='sales')
    batch = db.relationship('MedicineBatch', backref='sales')

    def __repr__(self):
        return f'<MedicineSaleItem {self.medicine.name} x{self.quantity}>'


# --- NEW MODELS FOR CHATBOT FUNCTIONALITY ---

class MedicineRequestStatus(Enum):
    PENDING = 'Pending'
    PROCESSING = 'Processing'
    DELIVERED = 'Delivered'
    CANCELLED = 'Cancelled'
    REJECTED = 'Rejected'


class MedicineRequest(db.Model):
    __tablename__ = 'medicine_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    requester_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(SqlEnum(MedicineRequestStatus), nullable=False, default=MedicineRequestStatus.PENDING)
    delivery_address = db.Column(db.String(255), nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00)
    notes = db.Column(db.Text, nullable=True)

    patient = db.relationship('Patient', back_populates='medicine_requests')
    requester = db.relationship('User', backref='made_medicine_requests')
    items = db.relationship('MedicineRequestItem', backref='request', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<MedicineRequest {self.id} for Patient {self.patient_id} - Status: {self.status.value}>'


class MedicineRequestItem(db.Model):
    __tablename__ = 'medicine_request_items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medicine_request_id = db.Column(db.Integer, db.ForeignKey('medicine_requests.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    requested_price_per_unit = db.Column(db.Numeric(10, 2), nullable=True)

    medicine = db.relationship('Medicine', back_populates='requested_items')

    def __repr__(self):
        return f'<MedicineRequestItem {self.medicine_id} x {self.quantity} for Request {self.medicine_request_id}>'
