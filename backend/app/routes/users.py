"""User management & RBAC routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.user_service import UserService
from app.events import event_bus
from app.utils.decorators import tenant_required

users_bp = Blueprint('users', __name__)


def _audit(action, **kwargs):
    """Helper to write audit log with request context."""
    claims = get_jwt()
    UserService.log_audit(
        action=action,
        tenant_id=claims.get('tenant_id'),
        user_id=get_jwt_identity(),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:500],
        **kwargs,
    )


def _emit(action, **kwargs):
    """Helper to emit an event with request context."""
    claims = get_jwt()
    event_bus.emit(
        action,
        tenant_id=claims.get('tenant_id'),
        user_id=get_jwt_identity(),
        data=kwargs,
    )


# ── Roles & Permissions ────────────────────────────────

@users_bp.route('/roles', methods=['GET'])
@jwt_required()
@tenant_required
def list_roles():
    """List all roles available for the current tenant."""
    claims = get_jwt()
    roles = UserService.list_roles(claims['tenant_id'])
    return jsonify({'roles': roles})


@users_bp.route('/permissions', methods=['GET'])
@jwt_required()
@tenant_required
def list_permissions():
    """List all system permissions."""
    perms = UserService.list_permissions()
    return jsonify({'permissions': perms})


@users_bp.route('/seed-roles', methods=['POST'])
@jwt_required()
@tenant_required
def seed_roles():
    """Seed default roles & permissions for current tenant."""
    claims = get_jwt()
    if claims.get('role') not in ('owner', 'admin') and not claims.get('is_platform_admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    count = UserService.seed_roles(claims['tenant_id'])
    return jsonify({'message': f'Seeded {count} roles', 'seeded': count})


# ── User CRUD ──────────────────────────────────────────

@users_bp.route('/', methods=['GET'])
@jwt_required()
@tenant_required
def list_users():
    """List users in the current tenant."""
    claims = get_jwt()
    # Only owner/admin/manager can list users (or users.view perm)
    if claims.get('role') not in ('owner', 'admin', 'manager') and not claims.get('is_platform_admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    result = UserService.list_users(
        tenant_id=claims['tenant_id'],
        search=request.args.get('search'),
        role_slug=request.args.get('role'),
        is_active=request.args.get('is_active', type=lambda v: v.lower() == 'true') if request.args.get('is_active') else None,
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 20, type=int),
    )
    return jsonify(result)


@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_user(user_id):
    """Get a single user."""
    claims = get_jwt()
    user = UserService.get_user(user_id, claims['tenant_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()})


@users_bp.route('/invite', methods=['POST'])
@jwt_required()
@tenant_required
def invite_user():
    """Invite a new user to the tenant."""
    claims = get_jwt()
    if claims.get('role') not in ('owner', 'admin') and not claims.get('is_platform_admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    required = ['email', 'first_name', 'last_name']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    # Cannot assign a role higher than your own
    caller_role = claims.get('role', 'user')
    target_role = data.get('role', 'user')
    if target_role == 'owner' and caller_role != 'owner':
        return jsonify({'error': 'Only owners can assign the owner role'}), 403

    try:
        user = UserService.invite_user(
            tenant_id=claims['tenant_id'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role_slug=target_role,
            password=data.get('password'),
            invited_by=get_jwt_identity(),
        )
        _audit('user.invited', resource_type='user', resource_id=user.id,
               details={'email': user.email, 'role': target_role})
        _emit('user.invited', email=user.email, role=target_role, user_name=user.full_name)
        return jsonify({'message': 'User invited', 'user': user.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_user(user_id):
    """Update a user (role, name, etc.)."""
    claims = get_jwt()
    if claims.get('role') not in ('owner', 'admin') and not claims.get('is_platform_admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    # Cannot promote to owner unless you are owner
    if data.get('role') == 'owner' and claims.get('role') != 'owner':
        return jsonify({'error': 'Only owners can assign the owner role'}), 403

    try:
        user = UserService.update_user(
            user_id=user_id,
            tenant_id=claims['tenant_id'],
            data=data,
            updated_by=get_jwt_identity(),
        )
        _audit('user.updated', resource_type='user', resource_id=user.id,
               details={k: v for k, v in data.items() if k != 'password'})
        _emit('user.updated', email=user.email, user_name=user.full_name)
        return jsonify({'user': user.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@users_bp.route('/<user_id>/activate', methods=['PUT'])
@jwt_required()
@tenant_required
def activate_user(user_id):
    """Activate or deactivate a user."""
    claims = get_jwt()
    if claims.get('role') not in ('owner', 'admin') and not claims.get('is_platform_admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json() or {}
    is_active = data.get('is_active', True)

    try:
        user = UserService.set_active(user_id, claims['tenant_id'], is_active, get_jwt_identity())
        action = 'user.activated' if is_active else 'user.deactivated'
        _audit(action, resource_type='user', resource_id=user.id)
        _emit(action, email=user.email, user_name=user.full_name)
        return jsonify({'user': user.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@users_bp.route('/<user_id>', methods=['DELETE'])
@jwt_required()
@tenant_required
def delete_user(user_id):
    """Delete a user."""
    claims = get_jwt()
    if claims.get('role') not in ('owner', 'admin') and not claims.get('is_platform_admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    # Cannot delete yourself
    if user_id == get_jwt_identity():
        return jsonify({'error': 'Cannot delete yourself'}), 400

    try:
        UserService.delete_user(user_id, claims['tenant_id'])
        _audit('user.deleted', resource_type='user', resource_id=user_id)
        return jsonify({'message': 'User deleted'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Profile (self-service) ─────────────────────────────

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update own profile."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    try:
        user = UserService.update_profile(get_jwt_identity(), data)
        _audit('user.profile_updated', resource_type='user', resource_id=user.id)
        return jsonify({'user': user.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Audit Logs ─────────────────────────────────────────

@users_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@tenant_required
def get_audit_logs():
    """Get audit logs for the tenant."""
    claims = get_jwt()
    if claims.get('role') not in ('owner', 'admin') and not claims.get('is_platform_admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    result = UserService.list_audit_logs(
        tenant_id=claims['tenant_id'],
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 50, type=int),
        action=request.args.get('action'),
        user_id=request.args.get('user_id'),
        resource_type=request.args.get('resource_type'),
    )
    return jsonify(result)
