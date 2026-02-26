"""Role-based access control models."""
import uuid
from datetime import datetime, timezone
from app import db


# ── Association table: role ↔ permission (many-to-many) ──
role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.String(36), db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.String(36), db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
)


class Role(db.Model):
    """Named role scoped to a tenant (or system-wide if tenant_id is null)."""
    __tablename__ = 'roles'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=True,  # Null = system default role
        index=True,
    )
    name = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)  # Cannot be deleted
    level = db.Column(db.Integer, default=0, nullable=False)  # Higher = more privileged

    permissions = db.relationship(
        'Permission', secondary=role_permissions, backref='roles', lazy='joined',
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'slug', name='uq_role_tenant_slug'),
    )

    def has_permission(self, perm_slug):
        """Check if this role grants a specific permission."""
        return any(p.slug == perm_slug for p in self.permissions)

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'is_system': self.is_system,
            'level': self.level,
            'permissions': [p.slug for p in self.permissions],
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Role {self.slug}>'


class Permission(db.Model):
    """Granular permission (e.g. 'inventory.create', 'sales.delete')."""
    __tablename__ = 'permissions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    module = db.Column(db.String(50), nullable=False, index=True)  # e.g. 'inventory', 'sales'
    action = db.Column(db.String(50), nullable=False)  # e.g. 'view', 'create', 'edit', 'delete'
    slug = db.Column(db.String(100), nullable=False, unique=True)  # e.g. 'inventory.create'
    description = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'module': self.module,
            'action': self.action,
            'slug': self.slug,
            'description': self.description,
        }

    def __repr__(self):
        return f'<Permission {self.slug}>'


class AuditLog(db.Model):
    """Immutable audit trail for security-sensitive actions."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey('tenants.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.String(36), nullable=True)
    details = db.Column(db.JSON, default=dict)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user = db.relationship('User', backref='audit_logs', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<AuditLog {self.action} by user={self.user_id}>'


# ── Default system permissions ──────────────────────────

SYSTEM_PERMISSIONS = [
    # Organisation
    ('organisation', 'view', 'organisation.view', 'View organisation tree'),
    ('organisation', 'manage', 'organisation.manage', 'Create/edit/delete org units'),
    # Modules
    ('modules', 'view', 'modules.view', 'View available modules'),
    ('modules', 'manage', 'modules.manage', 'Install/uninstall modules'),
    # Inventory
    ('inventory', 'view', 'inventory.view', 'View products, warehouses, stock'),
    ('inventory', 'create', 'inventory.create', 'Create products, categories, warehouses'),
    ('inventory', 'edit', 'inventory.edit', 'Edit products, categories, warehouses'),
    ('inventory', 'delete', 'inventory.delete', 'Delete products, categories, warehouses'),
    ('inventory', 'adjust_stock', 'inventory.adjust_stock', 'Adjust stock levels'),
    # Sales
    ('sales', 'view', 'sales.view', 'View quotations, invoices, customers'),
    ('sales', 'create', 'sales.create', 'Create quotations, invoices'),
    ('sales', 'edit', 'sales.edit', 'Edit quotations, invoices'),
    ('sales', 'delete', 'sales.delete', 'Delete quotations, invoices'),
    ('sales', 'record_payment', 'sales.record_payment', 'Record payments'),
    # Purchasing
    ('purchasing', 'view', 'purchasing.view', 'View purchase orders, suppliers'),
    ('purchasing', 'create', 'purchasing.create', 'Create purchase orders, suppliers'),
    ('purchasing', 'edit', 'purchasing.edit', 'Edit purchase orders, suppliers'),
    ('purchasing', 'delete', 'purchasing.delete', 'Delete purchase orders, suppliers'),
    ('purchasing', 'receive', 'purchasing.receive', 'Receive goods'),
    # Users
    ('users', 'view', 'users.view', 'View tenant users'),
    ('users', 'invite', 'users.invite', 'Invite new users'),
    ('users', 'manage', 'users.manage', 'Edit/deactivate users & assign roles'),
    # Settings
    ('settings', 'view', 'settings.view', 'View tenant settings'),
    ('settings', 'manage', 'settings.manage', 'Manage tenant settings'),
    # Audit
    ('audit', 'view', 'audit.view', 'View audit logs'),
    # Events
    ('events', 'view', 'events.view', 'View event history'),
    ('events', 'replay', 'events.replay', 'Replay events'),
]

# ── Default system roles with permission assignments ────

SYSTEM_ROLES = [
    {
        'name': 'Owner',
        'slug': 'owner',
        'description': 'Full access to all features. Cannot be removed.',
        'level': 100,
        'permissions': '*',  # All permissions
    },
    {
        'name': 'Admin',
        'slug': 'admin',
        'description': 'Full access except owner-level actions.',
        'level': 80,
        'permissions': '*',
    },
    {
        'name': 'Manager',
        'slug': 'manager',
        'description': 'Can view and manage business data but not system settings or users.',
        'level': 60,
        'permissions': [
            'organisation.view', 'organisation.manage',
            'modules.view',
            'inventory.view', 'inventory.create', 'inventory.edit', 'inventory.adjust_stock',
            'sales.view', 'sales.create', 'sales.edit', 'sales.record_payment',
            'purchasing.view', 'purchasing.create', 'purchasing.edit', 'purchasing.receive',
            'settings.view',
        ],
    },
    {
        'name': 'User',
        'slug': 'user',
        'description': 'Standard user with view and create access.',
        'level': 10,
        'permissions': [
            'organisation.view',
            'modules.view',
            'inventory.view', 'inventory.create',
            'sales.view', 'sales.create',
            'purchasing.view', 'purchasing.create',
            'settings.view',
        ],
    },
    {
        'name': 'Viewer',
        'slug': 'viewer',
        'description': 'Read-only access to business data.',
        'level': 1,
        'permissions': [
            'organisation.view',
            'modules.view',
            'inventory.view',
            'sales.view',
            'purchasing.view',
        ],
    },
]
