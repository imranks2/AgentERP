"""Tenant management routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.tenant_service import TenantService
from app.utils.decorators import platform_admin_required, tenant_required

tenant_bp = Blueprint('tenants', __name__)


@tenant_bp.route('/', methods=['GET'])
@jwt_required()
@platform_admin_required
def list_tenants():
    """List all tenants (platform admin only)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    search = request.args.get('search')

    result = TenantService.list_tenants(
        page=page, per_page=per_page, status=status, search=search
    )
    return jsonify(result)


@tenant_bp.route('/<tenant_id>', methods=['GET'])
@jwt_required()
def get_tenant(tenant_id):
    """Get tenant details."""
    claims = get_jwt()

    # Allow platform admins to view any tenant, others only their own
    if not claims.get('is_platform_admin') and claims.get('tenant_id') != tenant_id:
        return jsonify({'error': 'Access denied'}), 403

    tenant = TenantService.get_tenant(tenant_id)
    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404

    return jsonify({'tenant': tenant.to_dict()})


@tenant_bp.route('/<tenant_id>', methods=['PUT'])
@jwt_required()
def update_tenant(tenant_id):
    """Update tenant details."""
    claims = get_jwt()

    # Allow platform admins or tenant admins
    if not claims.get('is_platform_admin'):
        if claims.get('tenant_id') != tenant_id or claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    try:
        tenant = TenantService.update_tenant(tenant_id, **data)
        return jsonify({'tenant': tenant.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@tenant_bp.route('/<tenant_id>/status', methods=['PUT'])
@jwt_required()
@platform_admin_required
def change_tenant_status(tenant_id):
    """Change tenant lifecycle status (platform admin only)."""
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    try:
        tenant = TenantService.change_status(tenant_id, data['status'])
        return jsonify({'tenant': tenant.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@tenant_bp.route('/<tenant_id>', methods=['DELETE'])
@jwt_required()
@platform_admin_required
def delete_tenant(tenant_id):
    """Delete a tenant (platform admin only)."""
    try:
        TenantService.delete_tenant(tenant_id)
        return jsonify({'message': 'Tenant deleted successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@tenant_bp.route('/stats', methods=['GET'])
@jwt_required()
@platform_admin_required
def tenant_stats():
    """Get tenant statistics (platform admin only)."""
    stats = TenantService.get_tenant_stats()
    return jsonify(stats)
