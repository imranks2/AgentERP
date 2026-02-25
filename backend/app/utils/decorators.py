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
    """Decorator to require specific roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') not in roles and not claims.get('is_platform_admin'):
                return jsonify({'error': 'Insufficient permissions'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
