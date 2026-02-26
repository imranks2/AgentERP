"""Organisation hierarchy API routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.utils.decorators import tenant_required
from app.services.organisation_service import OrganisationService

org_bp = Blueprint('organisation', __name__)


# ── Tree / listing endpoints ─────────────────────────────────


@org_bp.route('/tree', methods=['GET'])
@jwt_required()
@tenant_required
def get_tree():
    """Return the full org tree for the current tenant."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    tree = OrganisationService.get_tree(tenant_id)
    return jsonify({'tree': tree})


@org_bp.route('/', methods=['GET'])
@jwt_required()
@tenant_required
def list_units():
    """List organisation units with optional filters.

    Query params:
        parent_id – filter by parent (use "root" for root nodes)
        unit_type – filter by unit type
        search    – free-text name/code search
        include_inactive – "true" to include deactivated units
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    parent_id = request.args.get('parent_id')
    unit_type = request.args.get('unit_type')
    search = request.args.get('search')
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    units = OrganisationService.list_units(
        tenant_id,
        parent_id=parent_id,
        unit_type=unit_type,
        include_inactive=include_inactive,
        search=search,
    )
    return jsonify({'units': [u.to_dict() for u in units]})


@org_bp.route('/stats', methods=['GET'])
@jwt_required()
@tenant_required
def get_stats():
    """Organisation hierarchy statistics."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    stats = OrganisationService.get_stats(tenant_id)
    return jsonify({'stats': stats})


# ── CRUD endpoints ───────────────────────────────────────────


@org_bp.route('/', methods=['POST'])
@jwt_required()
@tenant_required
def create_unit():
    """Create a new organisation unit."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    data = request.get_json() or {}

    try:
        unit = OrganisationService.create_unit(tenant_id, data)
        return jsonify({'unit': unit.to_dict(include_breadcrumb=True)}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@org_bp.route('/<unit_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_unit(unit_id):
    """Get a single organisation unit with breadcrumb."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    unit = OrganisationService.get_unit(tenant_id, unit_id)
    if not unit:
        return jsonify({'error': 'Organisation unit not found'}), 404
    return jsonify({
        'unit': unit.to_dict(include_breadcrumb=True),
        'ancestors': OrganisationService.get_ancestors(tenant_id, unit_id),
    })


@org_bp.route('/<unit_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_unit(unit_id):
    """Update an organisation unit."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    data = request.get_json() or {}

    try:
        unit = OrganisationService.update_unit(tenant_id, unit_id, data)
        if not unit:
            return jsonify({'error': 'Organisation unit not found'}), 404
        return jsonify({'unit': unit.to_dict(include_breadcrumb=True)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@org_bp.route('/<unit_id>', methods=['DELETE'])
@jwt_required()
@tenant_required
def delete_unit(unit_id):
    """Delete an organisation unit.

    Query params:
        reassign_to – ID of unit to re-parent children to (optional)
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    reassign_to = request.args.get('reassign_to')

    try:
        OrganisationService.delete_unit(tenant_id, unit_id, reassign_to)
        return jsonify({'message': 'Organisation unit deleted'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Move / restructure ──────────────────────────────────────


@org_bp.route('/<unit_id>/move', methods=['PUT'])
@jwt_required()
@tenant_required
def move_unit(unit_id):
    """Move a unit (and its subtree) under a new parent.

    Body:
        new_parent_id – target parent ID (null to make root)
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    data = request.get_json() or {}
    new_parent_id = data.get('new_parent_id')

    try:
        unit = OrganisationService.move_unit(tenant_id, unit_id, new_parent_id)
        return jsonify({'unit': unit.to_dict(include_breadcrumb=True)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Subtree ──────────────────────────────────────────────────


@org_bp.route('/<unit_id>/subtree', methods=['GET'])
@jwt_required()
@tenant_required
def get_subtree(unit_id):
    """Return the subtree rooted at a given unit."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    tree = OrganisationService.get_subtree(tenant_id, unit_id)
    if tree is None:
        return jsonify({'error': 'Organisation unit not found'}), 404
    return jsonify({'tree': tree})


@org_bp.route('/<unit_id>/ancestors', methods=['GET'])
@jwt_required()
@tenant_required
def get_ancestors(unit_id):
    """Return the ancestor chain from root → immediate parent."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    ancestors = OrganisationService.get_ancestors(tenant_id, unit_id)
    if ancestors is None:
        return jsonify({'error': 'Organisation unit not found'}), 404
    return jsonify({'ancestors': ancestors})
