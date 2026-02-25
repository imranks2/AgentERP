"""Tenant context utilities for multi-tenant data isolation."""
from flask import g, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request


def get_current_tenant_id():
    """Get the current tenant ID from JWT identity or request context."""
    if hasattr(g, 'tenant_id'):
        return g.tenant_id

    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            return identity.get('tenant_id')
    except Exception:
        pass

    return None


def set_tenant_context(tenant_id):
    """Set the tenant context for the current request."""
    g.tenant_id = tenant_id


class TenantQueryMixin:
    """Mixin that auto-scopes queries to the current tenant.

    Usage:
        class MyModel(db.Model, TenantQueryMixin):
            tenant_id = db.Column(...)
    """

    @classmethod
    def tenant_query(cls):
        """Return a query filtered to the current tenant."""
        from app import db
        tenant_id = get_current_tenant_id()
        if tenant_id:
            return cls.query.filter_by(tenant_id=tenant_id)
        return cls.query.filter(False)  # Return empty if no tenant context
