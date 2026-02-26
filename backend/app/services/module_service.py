"""Module registry service – discovery, installation, dependency resolution."""
from app import db
from app.models.module import ModuleDefinition, TenantModule


# ── Default module definitions (seeded on first run) ─────────

DEFAULT_MODULES = [
    {
        'name': 'Inventory',
        'slug': 'inventory',
        'description': 'Track products, warehouses, stock levels, and movements. Manage categories, SKUs, reorder points, and real-time availability.',
        'icon': 'Package',
        'color': '#10b981',
        'category': 'operations',
        'is_core': True,
        'sort_order': 1,
        'dependencies': [],
    },
    {
        'name': 'Sales',
        'slug': 'sales',
        'description': 'Manage customers, quotations, invoices, and payments. Convert quotations to invoices, track payment status, and monitor receivables.',
        'icon': 'ShoppingCart',
        'color': '#3b82f6',
        'category': 'sales',
        'is_core': True,
        'sort_order': 2,
        'dependencies': ['inventory'],
    },
    {
        'name': 'Purchasing',
        'slug': 'purchasing',
        'description': 'Manage suppliers and purchase orders. Track order status, receive goods into inventory, and manage procurement workflows.',
        'icon': 'Truck',
        'color': '#f59e0b',
        'category': 'operations',
        'is_core': True,
        'sort_order': 3,
        'dependencies': ['inventory'],
    },
]


class ModuleService:
    """Module registry and per-tenant installation management."""

    @staticmethod
    def seed_modules():
        """Ensure all default module definitions exist."""
        for mod_data in DEFAULT_MODULES:
            existing = ModuleDefinition.query.filter_by(slug=mod_data['slug']).first()
            if not existing:
                m = ModuleDefinition(**mod_data)
                db.session.add(m)
        db.session.commit()

    @staticmethod
    def list_available_modules():
        """Return all active module definitions."""
        return ModuleDefinition.query.filter_by(is_active=True)\
            .order_by(ModuleDefinition.sort_order).all()

    @staticmethod
    def get_module_by_slug(slug):
        return ModuleDefinition.query.filter_by(slug=slug, is_active=True).first()

    # ── Per-tenant operations ────────────────────────────────

    @staticmethod
    def get_tenant_modules(tenant_id):
        """List all modules installed for a tenant."""
        return TenantModule.query.filter_by(tenant_id=tenant_id).all()

    @staticmethod
    def is_module_enabled(tenant_id, module_slug):
        """Check whether a specific module is enabled for a tenant."""
        tm = TenantModule.query.join(ModuleDefinition)\
            .filter(
                TenantModule.tenant_id == tenant_id,
                ModuleDefinition.slug == module_slug,
                TenantModule.is_enabled == True,  # noqa: E712
            ).first()
        return tm is not None

    @staticmethod
    def install_module(tenant_id, module_slug):
        """Install (enable) a module for a tenant, resolving dependencies.

        Returns list of installed module slugs (including deps).
        Raises ValueError on problems.
        """
        mod = ModuleDefinition.query.filter_by(slug=module_slug, is_active=True).first()
        if not mod:
            raise ValueError(f"Module '{module_slug}' not found")

        installed = []

        # Install dependencies first
        for dep_slug in (mod.dependencies or []):
            if not ModuleService.is_module_enabled(tenant_id, dep_slug):
                installed.extend(ModuleService.install_module(tenant_id, dep_slug))

        # Install this module if not already
        existing = TenantModule.query.filter_by(
            tenant_id=tenant_id, module_id=mod.id
        ).first()
        if existing:
            if not existing.is_enabled:
                existing.is_enabled = True
                db.session.commit()
                installed.append(module_slug)
        else:
            tm = TenantModule(tenant_id=tenant_id, module_id=mod.id, is_enabled=True)
            db.session.add(tm)
            db.session.commit()
            installed.append(module_slug)

        return installed

    @staticmethod
    def uninstall_module(tenant_id, module_slug):
        """Disable a module for a tenant (data is preserved).

        Raises ValueError if other installed modules depend on this one.
        """
        mod = ModuleDefinition.query.filter_by(slug=module_slug).first()
        if not mod:
            raise ValueError(f"Module '{module_slug}' not found")

        # Check reverse dependencies
        all_enabled = TenantModule.query.filter_by(
            tenant_id=tenant_id, is_enabled=True
        ).all()
        for tm in all_enabled:
            dep_def = tm.definition
            if dep_def and module_slug in (dep_def.dependencies or []):
                raise ValueError(
                    f"Cannot disable '{module_slug}' – module '{dep_def.slug}' depends on it. "
                    f"Disable '{dep_def.slug}' first."
                )

        existing = TenantModule.query.filter_by(
            tenant_id=tenant_id, module_id=mod.id
        ).first()
        if existing:
            existing.is_enabled = False
            db.session.commit()

    @staticmethod
    def get_tenant_module_slugs(tenant_id):
        """Return set of enabled module slugs for a tenant."""
        rows = db.session.query(ModuleDefinition.slug)\
            .join(TenantModule)\
            .filter(
                TenantModule.tenant_id == tenant_id,
                TenantModule.is_enabled == True,  # noqa: E712
            ).all()
        return {r[0] for r in rows}
