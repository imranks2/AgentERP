"""Module management API routes – install/uninstall modules per tenant."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from app.utils.decorators import tenant_required, role_required
from app.services.module_service import ModuleService

modules_bp = Blueprint('modules', __name__)


@modules_bp.route('/available', methods=['GET'])
@jwt_required()
@tenant_required
def list_available():
    """List all available modules with their install status for this tenant."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    modules = ModuleService.list_available_modules()
    enabled_slugs = ModuleService.get_tenant_module_slugs(tenant_id)
    result = []
    for m in modules:
        d = m.to_dict()
        d['installed'] = m.slug in enabled_slugs
        result.append(d)
    return jsonify({'modules': result})


@modules_bp.route('/installed', methods=['GET'])
@jwt_required()
@tenant_required
def list_installed():
    """List modules installed for the current tenant."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    installed = ModuleService.get_tenant_modules(tenant_id)
    return jsonify({'modules': [tm.to_dict() for tm in installed]})


@modules_bp.route('/<slug>/install', methods=['POST'])
@jwt_required()
@tenant_required
@role_required('owner', 'admin')
def install_module(slug):
    """Install a module for the current tenant (resolves dependencies)."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    try:
        installed = ModuleService.install_module(tenant_id, slug)
        return jsonify({
            'message': f'Module installed successfully',
            'installed': installed,
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@modules_bp.route('/<slug>/uninstall', methods=['POST'])
@jwt_required()
@tenant_required
@role_required('owner', 'admin')
def uninstall_module(slug):
    """Uninstall a module (blocks if other modules depend on it)."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    try:
        ModuleService.uninstall_module(tenant_id, slug)
        return jsonify({'message': 'Module uninstalled successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@modules_bp.route('/seed', methods=['POST'])
@jwt_required()
@tenant_required
@role_required('owner', 'admin')
def seed_modules():
    """Seed default module definitions (idempotent)."""
    ModuleService.seed_modules()
    return jsonify({'message': 'Modules seeded'})
