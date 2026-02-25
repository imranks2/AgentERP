"""Organisation hierarchy model – tree-based, unlimited depth.

Supports unit types such as:
  enterprise, legal_entity, business_unit, branch, department, project, cost_center, team

Every unit belongs to exactly one tenant and optionally has a parent unit,
forming a recursive tree.  A materialised path column (``path``) accelerates
subtree queries without recursive CTEs on every read.
"""
import uuid
from datetime import datetime, timezone
from app import db


class OrganisationUnit(db.Model):
    """Represents a single node in the organisation tree."""
    __tablename__ = 'organisation_units'

    # ── primary key ──────────────────────────────────────────
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))

    # ── tenant isolation ─────────────────────────────────────
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)

    # ── tree structure ───────────────────────────────────────
    parent_id = db.Column(db.String(36),
                          db.ForeignKey('organisation_units.id'),
                          nullable=True, index=True)
    path = db.Column(db.Text, nullable=False, default='',
                     doc='Materialised path of ancestor ids separated by "/"')
    depth = db.Column(db.Integer, nullable=False, default=0)

    # ── descriptive fields ───────────────────────────────────
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), nullable=True,
                     doc='Short code (e.g. "HQ", "DEPT-FIN")')
    unit_type = db.Column(db.String(50), nullable=False, default='department',
                          doc='enterprise | legal_entity | business_unit | branch | department | project | cost_center | team')
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # ── optional contact / address ───────────────────────────
    manager_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)

    # ── metadata ─────────────────────────────────────────────
    sort_order = db.Column(db.Integer, nullable=False, default=0,
                           doc='Sibling sort order')
    metadata_ = db.Column('metadata', db.JSON, default=dict)

    # ── timestamps ───────────────────────────────────────────
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── relationships ────────────────────────────────────────
    children = db.relationship(
        'OrganisationUnit',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='OrganisationUnit.sort_order',
    )

    # ── table constraints ────────────────────────────────────
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'code',
                            name='uq_org_unit_tenant_code'),
        db.Index('ix_org_unit_path', 'tenant_id', 'path'),
    )

    # ── valid unit types ─────────────────────────────────────
    VALID_UNIT_TYPES = [
        'enterprise',
        'legal_entity',
        'business_unit',
        'branch',
        'department',
        'project',
        'cost_center',
        'team',
    ]

    # ── helpers ──────────────────────────────────────────────

    def build_path(self):
        """Recompute ``path`` and ``depth`` from parent chain.

        Call after changing ``parent_id`` and before ``db.session.flush()``.
        """
        if self.parent:
            self.path = f"{self.parent.path}/{self.parent.id}" if self.parent.path else self.parent.id
            self.depth = self.parent.depth + 1
        else:
            self.path = ''
            self.depth = 0

    @property
    def ancestor_ids(self):
        """Return ordered list of ancestor IDs (root → immediate parent)."""
        if not self.path:
            return []
        return [seg for seg in self.path.split('/') if seg]

    @property
    def breadcrumb_path(self):
        """Return ancestor names for breadcrumb display (requires eager load)."""
        parts = []
        node = self.parent
        while node:
            parts.append({'id': node.id, 'name': node.name})
            node = node.parent
        parts.reverse()
        return parts

    def to_dict(self, include_children=False, include_breadcrumb=False):
        """Serialise unit to dictionary."""
        data = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'parent_id': self.parent_id,
            'name': self.name,
            'code': self.code,
            'unit_type': self.unit_type,
            'description': self.description,
            'is_active': self.is_active,
            'manager_name': self.manager_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'depth': self.depth,
            'path': self.path,
            'sort_order': self.sort_order,
            'metadata': self.metadata_,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_children:
            data['children'] = [
                c.to_dict(include_children=True)
                for c in self.children.order_by(OrganisationUnit.sort_order)
            ]
        if include_breadcrumb:
            data['breadcrumb'] = self.breadcrumb_path
        return data

    def __repr__(self):
        return f'<OrganisationUnit {self.name} ({self.unit_type})>'
