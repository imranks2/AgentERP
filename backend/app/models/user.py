"""User model for authentication and tenant access."""
import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """Platform user, scoped to a tenant (or platform admin)."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=True,  # Null for platform admins
        index=True
    )
    email = db.Column(db.String(255), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # Legacy string role
    role_id = db.Column(
        db.String(36),
        db.ForeignKey('roles.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    is_platform_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    invited_by = db.Column(db.String(36), nullable=True)
    invite_accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    role_obj = db.relationship('Role', backref='users', lazy='joined')

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

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'email', name='uq_tenant_email'),
    )

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches."""
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def has_permission(self, perm_slug):
        """Check if user has a specific permission via their role."""
        if self.is_platform_admin:
            return True
        if self.role_obj:
            return self.role_obj.has_permission(perm_slug)
        # Fallback: owner/admin string roles get all perms
        return self.role in ('owner', 'admin')

    @property
    def permissions(self):
        """Return list of permission slugs for this user."""
        if self.is_platform_admin or self.role in ('owner', 'admin'):
            from app.models.role import Permission
            return [p.slug for p in Permission.query.all()]
        if self.role_obj:
            return [p.slug for p in self.role_obj.permissions]
        return []

    def to_dict(self, include_sensitive=False):
        """Serialize user to dictionary."""
        data = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'role_id': self.role_id,
            'role_name': self.role_obj.name if self.role_obj else self.role.title(),
            'is_platform_admin': self.is_platform_admin,
            'is_active': self.is_active,
            'avatar_url': self.avatar_url,
            'permissions': self.permissions,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        return data

    def __repr__(self):
        return f'<User {self.email}>'
