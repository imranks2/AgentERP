"""Purchasing models – Suppliers, Purchase Orders, PO Receipts.

Flow: Purchase Order → Receive Goods → (optionally link to Supplier Invoice)
"""
import uuid
from datetime import datetime, timezone
from app import db


class Supplier(db.Model):
    """Vendor / supplier record."""
    __tablename__ = 'suppliers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True, doc='e.g. Net 30')
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    metadata_ = db.Column('metadata', db.JSON, default=dict)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'name': self.name, 'email': self.email,
            'phone': self.phone, 'company': self.company,
            'address': self.address, 'tax_id': self.tax_id,
            'payment_terms': self.payment_terms,
            'notes': self.notes, 'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class PurchaseOrder(db.Model):
    """Purchase order sent to a supplier."""
    __tablename__ = 'purchase_orders'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=False)
    number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft',
                       doc='draft | sent | partial | received | cancelled')
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    expected_date = db.Column(db.Date, nullable=True)
    warehouse_id = db.Column(db.String(36), db.ForeignKey('warehouses.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    terms = db.Column(db.Text, nullable=True)
    currency = db.Column(db.String(3), nullable=False, default='USD')

    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(14, 2), nullable=False, default=0)

    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    items = db.relationship('PurchaseOrderItem', backref='purchase_order',
                            lazy='dynamic', cascade='all, delete-orphan',
                            order_by='PurchaseOrderItem.sort_order')
    warehouse = db.relationship('Warehouse')
    creator = db.relationship('User', foreign_keys=[created_by])

    VALID_STATUSES = ['draft', 'sent', 'partial', 'received', 'cancelled']

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'number', name='uq_po_number'),
    )

    def recalculate(self):
        subtotal = sum(float(item.total) for item in self.items)
        tax = sum(float(item.tax_amount) for item in self.items)
        self.subtotal = subtotal
        self.tax_amount = tax
        self.total = subtotal + tax - float(self.discount_amount or 0)

    def to_dict(self, include_items=True):
        data = {
            'id': self.id, 'tenant_id': self.tenant_id,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'number': self.number, 'status': self.status,
            'date': self.date.isoformat() if self.date else None,
            'expected_date': self.expected_date.isoformat() if self.expected_date else None,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'notes': self.notes, 'currency': self.currency,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total': float(self.total),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_items:
            data['items'] = [i.to_dict() for i in self.items]
        return data


class PurchaseOrderItem(db.Model):
    """Line item on a purchase order."""
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id = db.Column(db.String(36), db.ForeignKey('purchase_orders.id'),
                                  nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    quantity = db.Column(db.Numeric(14, 2), nullable=False, default=1)
    received_qty = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    unit_price = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    discount_pct = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship('Product')

    def calculate(self):
        qty = float(self.quantity or 0)
        price = float(self.unit_price or 0)
        disc = float(self.discount_pct or 0) / 100.0
        subtotal = qty * price * (1 - disc)
        tax = subtotal * float(self.tax_rate or 0) / 100.0
        self.tax_amount = round(tax, 2)
        self.total = round(subtotal, 2)

    def to_dict(self):
        return {
            'id': self.id, 'purchase_order_id': self.purchase_order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'description': self.description,
            'quantity': float(self.quantity),
            'received_qty': float(self.received_qty),
            'unit_price': float(self.unit_price),
            'discount_pct': float(self.discount_pct),
            'tax_rate': float(self.tax_rate),
            'tax_amount': float(self.tax_amount),
            'total': float(self.total),
            'sort_order': self.sort_order,
        }
