"""Tenant model for multi-tenant SaaS platform."""
import uuid
from datetime import datetime, timezone
from app import db


class Tenant(db.Model):
    """Represents a tenant (organisation) on the platform.

    Lifecycle states:
        - trial: New tenant, limited feature access
        - active: Paying tenant with full plan access
        - suspended: Temporarily disabled (e.g., payment failure)
        - churned: Permanently deactivated
    """
    __tablename__ = 'tenants'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    domain = db.Column(db.String(255), unique=True, nullable=True)
    status = db.Column(
        db.String(20),
        nullable=False,
        default='trial',
        index=True
    )
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    settings = db.Column(db.JSON, default=dict)
    metadata_ = db.Column('metadata', db.JSON, default=dict)

    # Trial management
    trial_ends_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Timestamps
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
    users = db.relationship('User', backref='tenant', lazy='dynamic',
                            cascade='all, delete-orphan')
    subscription = db.relationship('Subscription', backref='tenant', uselist=False,
                                   cascade='all, delete-orphan')
    organisation_units = db.relationship('OrganisationUnit', backref='tenant',
                                         lazy='dynamic', cascade='all, delete-orphan')

    VALID_STATUSES = ['trial', 'active', 'suspended', 'churned']
    VALID_TRANSITIONS = {
        'trial': ['active', 'churned'],
        'active': ['suspended', 'churned'],
        'suspended': ['active', 'churned'],
        'churned': [],  # Terminal state
    }

    def transition_to(self, new_status):
        """Transition tenant to a new lifecycle state."""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        if new_status not in self.VALID_TRANSITIONS.get(self.status, []):
            raise ValueError(
                f"Cannot transition from '{self.status}' to '{new_status}'. "
                f"Allowed transitions: {self.VALID_TRANSITIONS.get(self.status, [])}"
            )
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    @property
    def is_active(self):
        """Check if tenant can use the platform."""
        return self.status in ('trial', 'active')

    def to_dict(self):
        """Serialize tenant to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'domain': self.domain,
            'status': self.status,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'logo_url': self.logo_url,
            'settings': self.settings,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<Tenant {self.name} ({self.status})>'
