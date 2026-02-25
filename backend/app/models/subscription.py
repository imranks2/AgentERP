"""Subscription and Plan models for feature gating."""
import uuid
from datetime import datetime, timezone
from app import db


class SubscriptionPlan(db.Model):
    """Defines available subscription plans (Free, Standard, Premium)."""
    __tablename__ = 'subscription_plans'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    price_yearly = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    max_users = db.Column(db.Integer, nullable=False, default=1)
    max_storage_gb = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    metadata_ = db.Column('metadata', db.JSON, default=dict)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    features = db.relationship('PlanFeature', backref='plan', lazy='dynamic',
                               cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', backref='plan', lazy='dynamic')

    def to_dict(self, include_features=False):
        """Serialize plan to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'price_monthly': float(self.price_monthly),
            'price_yearly': float(self.price_yearly),
            'currency': self.currency,
            'max_users': self.max_users,
            'max_storage_gb': self.max_storage_gb,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
        }
        if include_features:
            data['features'] = [f.to_dict() for f in self.features]
        return data

    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'


class PlanFeature(db.Model):
    """Feature flags and limits associated with a plan."""
    __tablename__ = 'plan_features'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=False)
    feature_key = db.Column(db.String(100), nullable=False)
    feature_name = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    limit_value = db.Column(db.Integer, nullable=True)  # None = unlimited
    metadata_ = db.Column('metadata', db.JSON, default=dict)

    __table_args__ = (
        db.UniqueConstraint('plan_id', 'feature_key', name='uq_plan_feature'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'feature_key': self.feature_key,
            'feature_name': self.feature_name,
            'enabled': self.enabled,
            'limit_value': self.limit_value,
        }

    def __repr__(self):
        return f'<PlanFeature {self.feature_key} ({self.plan_id})>'


class Subscription(db.Model):
    """Tenant's active subscription linking to a plan."""
    __tablename__ = 'subscriptions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey('tenants.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    plan_id = db.Column(
        db.String(36),
        db.ForeignKey('subscription_plans.id'),
        nullable=False
    )
    billing_cycle = db.Column(db.String(10), default='monthly', nullable=False)  # monthly, yearly
    status = db.Column(db.String(20), default='active', nullable=False)
    starts_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'plan_id': self.plan_id,
            'plan': self.plan.to_dict() if self.plan else None,
            'billing_cycle': self.billing_cycle,
            'status': self.status,
            'starts_at': self.starts_at.isoformat() if self.starts_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<Subscription {self.tenant_id} -> {self.plan_id}>'
