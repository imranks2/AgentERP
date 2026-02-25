"""Module system models – dynamic module discovery, per-tenant installation."""
import uuid
from datetime import datetime, timezone
from app import db


class ModuleDefinition(db.Model):
    """Platform-wide module definition (installed by admins or discovered from manifests)."""
    __tablename__ = 'module_definitions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=False, default='Package')
    color = db.Column(db.String(7), nullable=False, default='#6366f1')
    category = db.Column(db.String(50), nullable=False, default='core')
    version = db.Column(db.String(20), nullable=False, default='1.0.0')
    is_core = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    # JSON schema for the module's entities (drives dynamic CRUD)
    schema = db.Column(db.JSON, default=dict)
    # Dependencies (list of module slugs)
    dependencies = db.Column(db.JSON, default=list)
    # Plan requirement (minimum plan slug needed)
    min_plan = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    tenant_modules = db.relationship('TenantModule', backref='definition',
                                     lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'category': self.category,
            'version': self.version,
            'is_core': self.is_core,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'dependencies': self.dependencies or [],
            'min_plan': self.min_plan,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<ModuleDefinition {self.name}>'


class TenantModule(db.Model):
    """Per-tenant module installation state."""
    __tablename__ = 'tenant_modules'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    module_id = db.Column(db.String(36), db.ForeignKey('module_definitions.id'),
                          nullable=False)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    installed_at = db.Column(db.DateTime(timezone=True),
                             default=lambda: datetime.now(timezone.utc), nullable=False)
    settings = db.Column(db.JSON, default=dict)

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'module_id', name='uq_tenant_module'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'module_id': self.module_id,
            'module': self.definition.to_dict() if self.definition else None,
            'is_enabled': self.is_enabled,
            'installed_at': self.installed_at.isoformat(),
            'settings': self.settings,
        }

    def __repr__(self):
        return f'<TenantModule tenant={self.tenant_id} module={self.module_id}>'
