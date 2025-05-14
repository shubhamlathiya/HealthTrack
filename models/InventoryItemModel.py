from utils.config import db


class Item(db.Model):
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    min_quantity = db.Column(db.Integer, default=0)  # Add minimum quantity threshold
    is_restricted = db.Column(db.Boolean, default=False)  # If item requires approval

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    issued_items = db.relationship('IssuedItem', backref='item', lazy=True)

    def __repr__(self):
        return f'<Item {self.item_name}>'


class IssuedItem(db.Model):
    __tablename__ = 'issued_items'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    issued_to = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Issued')

    requested_by = db.Column(db.String(100))  # Who made the request
    approved_by = db.Column(db.String(100))  # Who approved the request
    department = db.Column(db.String(100), nullable=True)  # Department making the request
    purpose = db.Column(db.Text)  # Purpose of the request

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<IssuedItem {self.id} - {self.item.item_name}>'
