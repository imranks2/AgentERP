"""Sales models – Quotations, Sales Orders, Invoices, Payments.

Flow: Quotation → Sales Order → Invoice → Payment
Each transition is tracked and cross-referenced.
"""
import uuid
from datetime import datetime, timezone
from app import db


class Customer(db.Model):
    """Customer / client record."""
    __tablename__ = 'customers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    metadata_ = db.Column('metadata', db.JSON, default=dict)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    quotations = db.relationship('Quotation', backref='customer', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='customer', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'name': self.name, 'email': self.email,
            'phone': self.phone, 'company': self.company,
            'address': self.address, 'tax_id': self.tax_id,
            'notes': self.notes, 'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class Quotation(db.Model):
    """Sales quotation / estimate that can be converted to an invoice."""
    __tablename__ = 'quotations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft',
                       doc='draft | sent | accepted | rejected | converted | expired')
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    valid_until = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    terms = db.Column(db.Text, nullable=True)
    currency = db.Column(db.String(3), nullable=False, default='USD')

    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(14, 2), nullable=False, default=0)

    # Link to the invoice created from this quotation
    invoice_id = db.Column(db.String(36), db.ForeignKey('invoices.id'), nullable=True)

    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    items = db.relationship('QuotationItem', backref='quotation', lazy='dynamic',
                            cascade='all, delete-orphan',
                            order_by='QuotationItem.sort_order')
    creator = db.relationship('User', foreign_keys=[created_by])

    VALID_STATUSES = ['draft', 'sent', 'accepted', 'rejected', 'converted', 'expired']

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'number', name='uq_quotation_number'),
    )

    def recalculate(self):
        """Recalculate totals from line items."""
        subtotal = sum(float(item.total) for item in self.items)
        tax = sum(float(item.tax_amount) for item in self.items)
        self.subtotal = subtotal
        self.tax_amount = tax
        self.total = subtotal + tax - float(self.discount_amount or 0)

    def to_dict(self, include_items=True):
        data = {
            'id': self.id, 'tenant_id': self.tenant_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'number': self.number, 'status': self.status,
            'date': self.date.isoformat() if self.date else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'notes': self.notes, 'terms': self.terms,
            'currency': self.currency,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total': float(self.total),
            'invoice_id': self.invoice_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_items:
            data['items'] = [i.to_dict() for i in self.items]
        return data


class QuotationItem(db.Model):
    """Line item on a quotation."""
    __tablename__ = 'quotation_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quotation_id = db.Column(db.String(36), db.ForeignKey('quotations.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    quantity = db.Column(db.Numeric(14, 2), nullable=False, default=1)
    unit_price = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    discount_pct = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship('Product')

    def calculate(self):
        """Compute line total from qty, price, discount, tax."""
        qty = float(self.quantity or 0)
        price = float(self.unit_price or 0)
        disc = float(self.discount_pct or 0) / 100.0
        subtotal = qty * price * (1 - disc)
        tax = subtotal * float(self.tax_rate or 0) / 100.0
        self.tax_amount = round(tax, 2)
        self.total = round(subtotal, 2)

    def to_dict(self):
        return {
            'id': self.id, 'quotation_id': self.quotation_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'description': self.description,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'discount_pct': float(self.discount_pct),
            'tax_rate': float(self.tax_rate),
            'tax_amount': float(self.tax_amount),
            'total': float(self.total),
            'sort_order': self.sort_order,
        }


class Invoice(db.Model):
    """Sales invoice – can be created directly or from a quotation."""
    __tablename__ = 'invoices'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    quotation_id = db.Column(db.String(36), nullable=True,
                             doc='Source quotation if converted')
    number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft',
                       doc='draft | sent | partial | paid | overdue | cancelled')
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    terms = db.Column(db.Text, nullable=True)
    currency = db.Column(db.String(3), nullable=False, default='USD')

    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    amount_paid = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    balance_due = db.Column(db.Numeric(14, 2), nullable=False, default=0)

    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic',
                            cascade='all, delete-orphan',
                            order_by='InvoiceItem.sort_order')
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic',
                               cascade='all, delete-orphan')
    source_quotation = db.relationship('Quotation', foreign_keys=[Quotation.invoice_id],
                                        backref='converted_invoice', uselist=False,
                                        viewonly=True)
    creator = db.relationship('User', foreign_keys=[created_by])

    VALID_STATUSES = ['draft', 'sent', 'partial', 'paid', 'overdue', 'cancelled']

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'number', name='uq_invoice_number'),
    )

    def recalculate(self):
        subtotal = sum(float(item.total) for item in self.items)
        tax = sum(float(item.tax_amount) for item in self.items)
        self.subtotal = subtotal
        self.tax_amount = tax
        self.total = subtotal + tax - float(self.discount_amount or 0)
        self.balance_due = float(self.total) - float(self.amount_paid or 0)

    def update_payment_status(self):
        """Recalculate amount_paid and set status accordingly."""
        paid = sum(float(p.amount) for p in self.payments.filter_by(status='completed'))
        self.amount_paid = paid
        self.balance_due = float(self.total) - paid
        if paid >= float(self.total):
            self.status = 'paid'
        elif paid > 0:
            self.status = 'partial'

    def to_dict(self, include_items=True, include_payments=False):
        data = {
            'id': self.id, 'tenant_id': self.tenant_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'quotation_id': self.quotation_id,
            'number': self.number, 'status': self.status,
            'date': self.date.isoformat() if self.date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'notes': self.notes, 'terms': self.terms,
            'currency': self.currency,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total': float(self.total),
            'amount_paid': float(self.amount_paid),
            'balance_due': float(self.balance_due),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_items:
            data['items'] = [i.to_dict() for i in self.items]
        if include_payments:
            data['payments'] = [p.to_dict() for p in self.payments]
        return data


class InvoiceItem(db.Model):
    """Line item on an invoice."""
    __tablename__ = 'invoice_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column(db.String(36), db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    quantity = db.Column(db.Numeric(14, 2), nullable=False, default=1)
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
            'id': self.id, 'invoice_id': self.invoice_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'description': self.description,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'discount_pct': float(self.discount_pct),
            'tax_rate': float(self.tax_rate),
            'tax_amount': float(self.tax_amount),
            'total': float(self.total),
            'sort_order': self.sort_order,
        }


class Payment(db.Model):
    """Payment received against an invoice."""
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    invoice_id = db.Column(db.String(36), db.ForeignKey('invoices.id'), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False, default='bank_transfer',
                               doc='cash | bank_transfer | credit_card | cheque | other')
    reference = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='completed',
                       doc='completed | pending | failed | refunded')
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    notes = db.Column(db.Text, nullable=True)

    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    creator = db.relationship('User', foreign_keys=[created_by])

    VALID_METHODS = ['cash', 'bank_transfer', 'credit_card', 'cheque', 'other']

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'invoice_id': self.invoice_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'reference': self.reference,
            'status': self.status,
            'date': self.date.isoformat() if self.date else None,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
        }
