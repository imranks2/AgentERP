"""Authorization decorators for route protection."""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt


def platform_admin_required(fn):
    """Decorator to require platform admin role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get('is_platform_admin'):
            return jsonify({'error': 'Platform admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


def tenant_required(fn):
    """Decorator to require a valid tenant context."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get('tenant_id'):
            return jsonify({'error': 'Tenant context required'}), 403
        return fn(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Decorator to require specific roles (by slug)."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('is_platform_admin'):
                return fn(*args, **kwargs)
            if claims.get('role') not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def permission_required(*perms):
    """Decorator to require specific permissions (by slug).

    Usage:
        @permission_required('inventory.create')
        @permission_required('sales.view', 'sales.create')  # any of these
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            # Platform admins bypass
            if claims.get('is_platform_admin'):
                return fn(*args, **kwargs)
            # Owner/admin bypass (full access)
            if claims.get('role') in ('owner', 'admin'):
                return fn(*args, **kwargs)
            # Check permissions from JWT claims
            user_perms = set(claims.get('permissions', []))
            if not user_perms.intersection(perms):
                return jsonify({'error': 'Insufficient permissions'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
