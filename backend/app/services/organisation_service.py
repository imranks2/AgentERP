"""Organisation hierarchy business logic."""
from app import db
from app.models.organisation import OrganisationUnit


class OrganisationService:
    """CRUD and tree operations for organisation units."""

    # ── Create ───────────────────────────────────────────────

    @staticmethod
    def create_unit(tenant_id, data):
        """Create a new organisation unit.

        Args:
            tenant_id: Owning tenant ID
            data: dict with name, unit_type, parent_id (optional), etc.

        Returns:
            The newly created OrganisationUnit

        Raises:
            ValueError on validation errors
        """
        name = data.get('name', '').strip()
        if not name:
            raise ValueError('Name is required')

        unit_type = data.get('unit_type', 'department')
        if unit_type not in OrganisationUnit.VALID_UNIT_TYPES:
            raise ValueError(
                f"Invalid unit_type '{unit_type}'. "
                f"Valid types: {', '.join(OrganisationUnit.VALID_UNIT_TYPES)}"
            )

        parent_id = data.get('parent_id')
        parent = None
        if parent_id:
            parent = OrganisationUnit.query.filter_by(
                id=parent_id, tenant_id=tenant_id
            ).first()
            if not parent:
                raise ValueError('Parent unit not found or belongs to another tenant')

        code = data.get('code', '').strip() or None
        if code:
            existing = OrganisationUnit.query.filter_by(
                tenant_id=tenant_id, code=code
            ).first()
            if existing:
                raise ValueError(f"Code '{code}' already exists in this tenant")

        unit = OrganisationUnit(
            tenant_id=tenant_id,
            parent_id=parent_id,
            name=name,
            code=code,
            unit_type=unit_type,
            description=data.get('description'),
            is_active=data.get('is_active', True),
            manager_name=data.get('manager_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            sort_order=data.get('sort_order', 0),
            metadata_=data.get('metadata', {}),
        )

        # set parent so build_path() can walk the chain
        if parent:
            unit.parent = parent
        unit.build_path()

        db.session.add(unit)
        db.session.commit()
        return unit

    # ── Read ─────────────────────────────────────────────────

    @staticmethod
    def get_unit(tenant_id, unit_id):
        """Get a single unit with breadcrumb."""
        return OrganisationUnit.query.filter_by(
            id=unit_id, tenant_id=tenant_id
        ).first()

    @staticmethod
    def list_units(tenant_id, parent_id=None, unit_type=None,
                   include_inactive=False, search=None):
        """List units with optional filters.

        Args:
            tenant_id: Tenant scope
            parent_id: Filter by parent (None = root nodes when explicitly set)
            unit_type: Filter by unit type
            include_inactive: Whether to include deactivated units
            search: Free-text search on name / code

        Returns:
            List of OrganisationUnit
        """
        q = OrganisationUnit.query.filter_by(tenant_id=tenant_id)

        if parent_id is not None:
            if parent_id == 'root':
                q = q.filter(OrganisationUnit.parent_id.is_(None))
            else:
                q = q.filter_by(parent_id=parent_id)

        if unit_type:
            q = q.filter_by(unit_type=unit_type)

        if not include_inactive:
            q = q.filter_by(is_active=True)

        if search:
            like = f'%{search}%'
            q = q.filter(
                db.or_(
                    OrganisationUnit.name.ilike(like),
                    OrganisationUnit.code.ilike(like),
                )
            )

        return q.order_by(
            OrganisationUnit.depth,
            OrganisationUnit.sort_order,
            OrganisationUnit.name,
        ).all()

    @staticmethod
    def get_tree(tenant_id):
        """Return the full org tree for a tenant as nested dicts.

        Fetches all units in one query and assembles them in memory.
        """
        units = OrganisationUnit.query.filter_by(
            tenant_id=tenant_id, is_active=True
        ).order_by(
            OrganisationUnit.depth,
            OrganisationUnit.sort_order,
            OrganisationUnit.name,
        ).all()

        lookup = {}
        roots = []

        for u in units:
            node = u.to_dict(include_children=False)
            node['children'] = []
            lookup[u.id] = node

        for u in units:
            node = lookup[u.id]
            if u.parent_id and u.parent_id in lookup:
                lookup[u.parent_id]['children'].append(node)
            else:
                roots.append(node)

        return roots

    @staticmethod
    def get_subtree(tenant_id, unit_id):
        """Return a subtree rooted at *unit_id* using the materialised path."""
        root = OrganisationUnit.query.filter_by(
            id=unit_id, tenant_id=tenant_id
        ).first()
        if not root:
            return None

        # All descendants share a path prefix containing this unit's id
        path_prefix = f"{root.path}/{root.id}" if root.path else root.id
        descendants = OrganisationUnit.query.filter(
            OrganisationUnit.tenant_id == tenant_id,
            OrganisationUnit.is_active == True,  # noqa: E712
            db.or_(
                OrganisationUnit.id == unit_id,
                OrganisationUnit.path.like(f'{path_prefix}%'),
            ),
        ).order_by(
            OrganisationUnit.depth,
            OrganisationUnit.sort_order,
        ).all()

        lookup = {}
        result = None

        for u in descendants:
            node = u.to_dict()
            node['children'] = []
            lookup[u.id] = node

        for u in descendants:
            node = lookup[u.id]
            if u.id == unit_id:
                result = node
            elif u.parent_id in lookup:
                lookup[u.parent_id]['children'].append(node)

        return result

    @staticmethod
    def get_ancestors(tenant_id, unit_id):
        """Return list of ancestors from root → immediate parent."""
        unit = OrganisationUnit.query.filter_by(
            id=unit_id, tenant_id=tenant_id
        ).first()
        if not unit:
            return None
        ancestor_ids = unit.ancestor_ids
        if not ancestor_ids:
            return []
        ancestors = OrganisationUnit.query.filter(
            OrganisationUnit.id.in_(ancestor_ids),
            OrganisationUnit.tenant_id == tenant_id,
        ).all()
        # Order by depth
        id_map = {a.id: a for a in ancestors}
        return [id_map[aid].to_dict() for aid in ancestor_ids if aid in id_map]

    # ── Update ───────────────────────────────────────────────

    @staticmethod
    def update_unit(tenant_id, unit_id, data):
        """Update an organisation unit's properties.

        Returns:
            Updated OrganisationUnit or None
        """
        unit = OrganisationUnit.query.filter_by(
            id=unit_id, tenant_id=tenant_id
        ).first()
        if not unit:
            return None

        updatable = [
            'name', 'description', 'unit_type', 'is_active',
            'manager_name', 'email', 'phone', 'address',
            'sort_order', 'code',
        ]

        for field in updatable:
            if field in data:
                value = data[field]
                if field == 'unit_type' and value not in OrganisationUnit.VALID_UNIT_TYPES:
                    raise ValueError(f"Invalid unit_type '{value}'")
                if field == 'code' and value:
                    existing = OrganisationUnit.query.filter(
                        OrganisationUnit.tenant_id == tenant_id,
                        OrganisationUnit.code == value,
                        OrganisationUnit.id != unit_id,
                    ).first()
                    if existing:
                        raise ValueError(f"Code '{value}' already exists")
                setattr(unit, field, value)

        db.session.commit()
        return unit

    @staticmethod
    def move_unit(tenant_id, unit_id, new_parent_id):
        """Move a unit (and its subtree) to a new parent.

        Prevents:
            - Moving a node under itself or its descendant (cycle)
            - Cross-tenant moves

        Updates materialised path for the moved node and all descendants.
        """
        unit = OrganisationUnit.query.filter_by(
            id=unit_id, tenant_id=tenant_id
        ).first()
        if not unit:
            raise ValueError('Unit not found')

        new_parent = None
        if new_parent_id:
            new_parent = OrganisationUnit.query.filter_by(
                id=new_parent_id, tenant_id=tenant_id
            ).first()
            if not new_parent:
                raise ValueError('New parent not found')

            # Cycle detection: new parent must not be a descendant of unit
            if new_parent_id == unit_id:
                raise ValueError('Cannot move a unit under itself')
            old_prefix = f"{unit.path}/{unit.id}" if unit.path else unit.id
            if new_parent.path and old_prefix in new_parent.path:
                raise ValueError('Cannot move a unit under its own descendant')

        # Compute old path prefix for descendants
        old_prefix = f"{unit.path}/{unit.id}" if unit.path else unit.id

        # Update the unit itself
        unit.parent_id = new_parent_id
        unit.parent = new_parent
        unit.build_path()
        new_prefix = f"{unit.path}/{unit.id}" if unit.path else unit.id

        # Update all descendants' paths
        descendants = OrganisationUnit.query.filter(
            OrganisationUnit.tenant_id == tenant_id,
            OrganisationUnit.path.like(f'{old_prefix}%'),
            OrganisationUnit.id != unit_id,
        ).all()

        for desc in descendants:
            desc.path = desc.path.replace(old_prefix, new_prefix, 1)
            desc.depth = len([s for s in desc.path.split('/') if s])

        db.session.commit()
        return unit

    # ── Delete ───────────────────────────────────────────────

    @staticmethod
    def delete_unit(tenant_id, unit_id, reassign_children_to=None):
        """Delete an organisation unit.

        Args:
            tenant_id: Tenant scope
            unit_id: Unit to delete
            reassign_children_to: If provided, children are re-parented.
                If None, children are *also* deleted (cascade).
        """
        unit = OrganisationUnit.query.filter_by(
            id=unit_id, tenant_id=tenant_id
        ).first()
        if not unit:
            raise ValueError('Unit not found')

        if reassign_children_to is not None:
            new_parent = None
            if reassign_children_to:
                new_parent = OrganisationUnit.query.filter_by(
                    id=reassign_children_to, tenant_id=tenant_id
                ).first()
                if not new_parent:
                    raise ValueError('Reassignment target not found')

            children = OrganisationUnit.query.filter_by(
                parent_id=unit_id, tenant_id=tenant_id
            ).all()
            for child in children:
                child.parent_id = reassign_children_to
                child.parent = new_parent
                child.build_path()
                # Update child's descendants paths
                OrganisationService._rebuild_descendant_paths(tenant_id, child)

        db.session.delete(unit)
        db.session.commit()

    @staticmethod
    def _rebuild_descendant_paths(tenant_id, unit):
        """Recursively rebuild paths for all descendants of a unit."""
        children = OrganisationUnit.query.filter_by(
            parent_id=unit.id, tenant_id=tenant_id
        ).all()
        for child in children:
            child.parent = unit
            child.build_path()
            OrganisationService._rebuild_descendant_paths(tenant_id, child)

    # ── Stats ────────────────────────────────────────────────

    @staticmethod
    def get_stats(tenant_id):
        """Summary statistics for the org hierarchy."""
        base = OrganisationUnit.query.filter_by(tenant_id=tenant_id)
        total = base.count()
        active = base.filter_by(is_active=True).count()
        by_type = (
            db.session.query(
                OrganisationUnit.unit_type,
                db.func.count(OrganisationUnit.id),
            )
            .filter_by(tenant_id=tenant_id, is_active=True)
            .group_by(OrganisationUnit.unit_type)
            .all()
        )
        max_depth = (
            db.session.query(db.func.max(OrganisationUnit.depth))
            .filter_by(tenant_id=tenant_id, is_active=True)
            .scalar()
        ) or 0

        return {
            'total_units': total,
            'active_units': active,
            'inactive_units': total - active,
            'max_depth': max_depth,
            'by_type': {t: c for t, c in by_type},
        }
