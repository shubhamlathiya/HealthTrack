from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from utils.config import db


class ItemCategory(db.Model):
    __tablename__ = 'item_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    items = db.relationship('Item', back_populates='category', lazy='dynamic', cascade="all, delete-orphan")

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<ItemCategory {self.name}>'


class ItemStore(db.Model):
    __tablename__ = 'item_stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    stock_code = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text)

    item_stocks = db.relationship('ItemStock', back_populates='store', lazy='dynamic', cascade="all, delete-orphan")

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<ItemStore {self.name}>'


class ItemSupplier(db.Model):
    __tablename__ = 'item_suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    contact_person_name = db.Column(db.String(100))
    address = db.Column(db.Text)
    contact_person_phone = db.Column(db.String(20))
    contact_person_email = db.Column(db.String(100))
    description = db.Column(db.Text)

    supplied_stocks = db.relationship('ItemStock', back_populates='supplier', lazy='dynamic', cascade="all, delete-orphan")

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<ItemSupplier {self.name}>'

class Item(db.Model):
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('item_categories.id'), nullable=False)
    description = db.Column(db.Text)
    min_quantity = db.Column(db.Integer, default=0)
    is_restricted = db.Column(db.Boolean, default=False)

    category = db.relationship('ItemCategory', back_populates='items') # Added back_populates here
    item_stocks = db.relationship('ItemStock', back_populates='item', lazy='dynamic', cascade="all, delete-orphan")
    issued_items = db.relationship('IssuedItem', back_populates='item', lazy='dynamic', cascade="all, delete-orphan")

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    @hybrid_property
    def total_stock(self):
        return db.session.query(func.sum(ItemStock.quantity)).filter(
            ItemStock.item_id == self.id,
            ItemStock.is_deleted == False
        ).scalar() or 0

    @total_stock.expression
    def total_stock(cls):
        return db.session.query(func.sum(ItemStock.quantity)).filter(
            ItemStock.item_id == cls.id,
            ItemStock.is_deleted == False
        ).label('total_stock')

    @hybrid_property
    def total_issued_quantity(self):
        return db.session.query(func.sum(IssuedItem.quantity)).filter(
            IssuedItem.item_id == self.id,
            IssuedItem.is_deleted == False,
            IssuedItem.status.in_(['Issued', 'Pending'])
        ).scalar() or 0

    @total_issued_quantity.expression
    def total_issued_quantity(cls):
        return db.session.query(func.sum(IssuedItem.quantity)).filter(
            IssuedItem.item_id == cls.id,
            IssuedItem.is_deleted == False,
            IssuedItem.status.in_(['Issued', 'Pending'])
        ).label('total_issued_quantity')

    @hybrid_property
    def available_stock(self):
        return self.total_stock - self.total_issued_quantity

    @available_stock.expression
    def available_stock(cls):
        return (cls.total_stock - cls.total_issued_quantity).label('available_stock')

    def __repr__(self):
        return f'<Item {self.item_name}>'


class ItemStock(db.Model):
    __tablename__ = 'item_stocks'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('item_suppliers.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('item_stores.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False, default=db.func.current_date())
    selling_price = db.Column(db.Float, nullable=True)  # New field
    batch_number = db.Column(db.String(100), nullable=True)  # New field
    manufacture_date = db.Column(db.DateTime, nullable=True)  # New field
    expiry_date = db.Column(db.DateTime, nullable=True)  # New field
    description = db.Column(db.Text)
    document_path = db.Column(db.String(255), nullable=True)

    item = db.relationship('Item', back_populates='item_stocks', lazy='joined', primaryjoin="ItemStock.item_id == Item.id")
    supplier = db.relationship('ItemSupplier', back_populates='supplied_stocks', lazy='joined', primaryjoin="ItemStock.supplier_id == ItemSupplier.id")
    store = db.relationship('ItemStore', back_populates='item_stocks', lazy='joined', primaryjoin="ItemStock.store_id == ItemStore.id")

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        try:
            return f'<ItemStock {self.item.item_name} - {self.quantity} in {self.store.name}>'
        except AttributeError:
            return f'<ItemStock {self.id} - item_id: {self.item_id}>'


class IssuedItem(db.Model):
    __tablename__ = 'issued_items'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    issued_to_name = db.Column(db.String(100), nullable=False)
    issued_to_user_id = db.Column(db.String(50), nullable=True)
    user_type = db.Column(db.String(50), nullable=False)
    issued_by = db.Column(db.String(100), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Issued')
    note = db.Column(db.Text)

    requested_by = db.Column(db.String(100), nullable=True)
    approved_by = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    purpose = db.Column(db.Text, nullable=True)

    # Relationship to Item: An IssuedItem belongs to one Item
    item = db.relationship('Item', back_populates='issued_items', lazy='joined', primaryjoin="IssuedItem.item_id == Item.id")

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        try:
            return f'<IssuedItem {self.id} - {self.item.item_name} to {self.issued_to_name}>'
        except AttributeError:
            return f'<IssuedItem {self.id} - item_id: {self.item_id}>'