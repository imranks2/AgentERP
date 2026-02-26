"""CRM models – Phase 8.

Leads, opportunities pipeline, activities, and campaigns.
"""
import uuid
from datetime import datetime, timezone
from app import db


def _uuid():
    return str(uuid.uuid4())


class Lead(db.Model):
    """Prospective contact / company."""
    __tablename__ = 'leads'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    company = db.Column(db.String(150), nullable=True)
    source = db.Column(db.String(30), default='web')  # web, referral, campaign, other
    status = db.Column(db.String(20), default='new')  # new, contacted, qualified, converted, lost
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    score = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    converted_customer_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    activities = db.relationship('CRMActivity', backref='lead', lazy='dynamic',
                                 foreign_keys='CRMActivity.lead_id')
    opportunities = db.relationship('Opportunity', backref='lead', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id, 'name': self.name,
            'email': self.email, 'phone': self.phone, 'company': self.company,
            'source': self.source, 'status': self.status, 'assigned_to': self.assigned_to,
            'score': self.score, 'notes': self.notes,
            'converted_customer_id': self.converted_customer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Opportunity(db.Model):
    """Potential deal in the sales pipeline."""
    __tablename__ = 'opportunities'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    lead_id = db.Column(db.String(36), db.ForeignKey('leads.id'), nullable=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='USD')
    stage = db.Column(db.String(30), default='prospecting')  # prospecting, proposal, negotiation, won, lost
    probability = db.Column(db.Integer, default=10)  # 0-100
    expected_close_date = db.Column(db.Date, nullable=True)
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    activities = db.relationship('CRMActivity', backref='opportunity', lazy='dynamic',
                                 foreign_keys='CRMActivity.opportunity_id')

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id, 'lead_id': self.lead_id,
            'customer_id': self.customer_id, 'title': self.title,
            'value': self.value, 'currency': self.currency,
            'stage': self.stage, 'probability': self.probability,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'assigned_to': self.assigned_to, 'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CRMActivity(db.Model):
    """Interaction log — calls, emails, meetings, notes."""
    __tablename__ = 'crm_activities'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    activity_type = db.Column(db.String(20), nullable=False)  # call, email, meeting, note
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    lead_id = db.Column(db.String(36), db.ForeignKey('leads.id'), nullable=True)
    opportunity_id = db.Column(db.String(36), db.ForeignKey('opportunities.id'), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'activity_type': self.activity_type, 'subject': self.subject,
            'description': self.description,
            'date': self.date.isoformat() if self.date else None,
            'lead_id': self.lead_id, 'opportunity_id': self.opportunity_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
