"""Accounting models – Phase 8.

Double-entry bookkeeping with chart of accounts, journal entries,
fiscal periods, tax rates, and currency management.
"""
import uuid
from datetime import datetime, timezone, date
from app import db


def _uuid():
    return str(uuid.uuid4())


class Account(db.Model):
    """Chart of accounts entry."""
    __tablename__ = 'accounts'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    account_type = db.Column(db.String(30), nullable=False)  # asset, liability, equity, revenue, expense
    parent_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=True)
    currency = db.Column(db.String(3), default='USD')
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    children = db.relationship('Account', backref=db.backref('parent', remote_side='Account.id'), lazy='dynamic')
    journal_lines = db.relationship('JournalLine', backref='account', lazy='dynamic')

    __table_args__ = (db.UniqueConstraint('tenant_id', 'code', name='uq_account_code'),)

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id, 'code': self.code,
            'name': self.name, 'account_type': self.account_type,
            'parent_id': self.parent_id, 'currency': self.currency,
            'is_active': self.is_active, 'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FiscalYear(db.Model):
    """Financial year period."""
    __tablename__ = 'fiscal_years'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_closed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    periods = db.relationship('FiscalPeriod', backref='fiscal_year', lazy='dynamic',
                              cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id, 'name': self.name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_closed': self.is_closed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FiscalPeriod(db.Model):
    """Monthly period within a fiscal year."""
    __tablename__ = 'fiscal_periods'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    fiscal_year_id = db.Column(db.String(36), db.ForeignKey('fiscal_years.id'), nullable=False)
    period_number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_closed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id, 'period_number': self.period_number, 'name': self.name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_closed': self.is_closed,
        }


class JournalEntry(db.Model):
    """Header for a double-entry transaction."""
    __tablename__ = 'journal_entries'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    number = db.Column(db.String(30), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: date.today())
    reference_type = db.Column(db.String(30), nullable=True)  # invoice, payment, purchase, manual
    reference_id = db.Column(db.String(36), nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, posted, reversed
    total_debit = db.Column(db.Float, default=0)
    total_credit = db.Column(db.Float, default=0)
    created_by = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    posted_at = db.Column(db.DateTime, nullable=True)

    lines = db.relationship('JournalLine', backref='journal_entry', lazy='dynamic',
                            cascade='all, delete-orphan')

    __table_args__ = (db.UniqueConstraint('tenant_id', 'number', name='uq_journal_number'),)

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id, 'number': self.number,
            'date': self.date.isoformat() if self.date else None,
            'reference_type': self.reference_type, 'reference_id': self.reference_id,
            'description': self.description, 'status': self.status,
            'total_debit': self.total_debit, 'total_credit': self.total_credit,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'lines': [l.to_dict() for l in self.lines.all()],
        }


class JournalLine(db.Model):
    """Debit/credit line in a journal entry."""
    __tablename__ = 'journal_lines'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    journal_entry_id = db.Column(db.String(36), db.ForeignKey('journal_entries.id', ondelete='CASCADE'),
                                  nullable=False, index=True)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    debit = db.Column(db.Float, default=0)
    credit = db.Column(db.Float, default=0)
    description = db.Column(db.String(200), nullable=True)
    currency = db.Column(db.String(3), default='USD')
    exchange_rate = db.Column(db.Float, default=1.0)

    def to_dict(self):
        return {
            'id': self.id, 'journal_entry_id': self.journal_entry_id,
            'account_id': self.account_id, 'debit': self.debit, 'credit': self.credit,
            'description': self.description, 'currency': self.currency,
            'exchange_rate': self.exchange_rate,
            'account_name': self.account.name if self.account else None,
            'account_code': self.account.code if self.account else None,
        }


class TaxRate(db.Model):
    """Tax rate definition per jurisdiction."""
    __tablename__ = 'tax_rates'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    rate = db.Column(db.Float, nullable=False)  # e.g. 0.15 for 15%
    tax_type = db.Column(db.String(20), default='both')  # sales | purchase | both
    jurisdiction = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id, 'name': self.name,
            'code': self.code, 'rate': self.rate, 'tax_type': self.tax_type,
            'jurisdiction': self.jurisdiction, 'is_active': self.is_active,
        }


class CurrencyRate(db.Model):
    """Currency exchange rate table."""
    __tablename__ = 'currency_rates'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    code = db.Column(db.String(3), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(5), default='')
    exchange_rate = db.Column(db.Float, nullable=False, default=1.0)  # rate to base currency
    is_base = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('tenant_id', 'code', name='uq_currency_code'),)

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id, 'code': self.code,
            'name': self.name, 'symbol': self.symbol,
            'exchange_rate': self.exchange_rate, 'is_base': self.is_base,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
