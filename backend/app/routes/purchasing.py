"""Purchasing module API routes – Suppliers, Purchase Orders, Goods Receipt."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.utils.decorators import tenant_required
from app.services.purchasing_service import PurchasingService

purchasing_bp = Blueprint('purchasing', __name__)


def _module_check(tenant_id):
    from app.services.module_service import ModuleService
    if not ModuleService.is_module_enabled(tenant_id, 'purchasing'):
        return jsonify({'error': 'Purchasing module not enabled'}), 403
    return None


# ── Suppliers ────────────────────────────────────────────────

@purchasing_bp.route('/suppliers', methods=['GET'])
@jwt_required()
@tenant_required
def list_suppliers():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    suppliers, total = PurchasingService.list_suppliers(
        tenant_id,
        search=request.args.get('search'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify({
        'suppliers': [s.to_dict() for s in suppliers],
        'total': total,
    })


@purchasing_bp.route('/suppliers/<sup_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_supplier(sup_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    sup = PurchasingService.get_supplier(tenant_id, sup_id)
    if not sup:
        return jsonify({'error': 'Supplier not found'}), 404
    return jsonify({'supplier': sup.to_dict()})


@purchasing_bp.route('/suppliers', methods=['POST'])
@jwt_required()
@tenant_required
def create_supplier():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        sup = PurchasingService.create_supplier(tenant_id, request.get_json() or {})
        return jsonify({'supplier': sup.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@purchasing_bp.route('/suppliers/<sup_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_supplier(sup_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    sup = PurchasingService.update_supplier(tenant_id, sup_id, request.get_json() or {})
    if not sup:
        return jsonify({'error': 'Supplier not found'}), 404
    return jsonify({'supplier': sup.to_dict()})


# ── Purchase Orders ──────────────────────────────────────────

@purchasing_bp.route('/orders', methods=['GET'])
@jwt_required()
@tenant_required
def list_orders():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    orders, total = PurchasingService.list_purchase_orders(
        tenant_id,
        status=request.args.get('status'),
        supplier_id=request.args.get('supplier_id'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify({
        'orders': [o.to_dict() for o in orders],
        'total': total,
    })


@purchasing_bp.route('/orders/<po_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_order(po_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    po = PurchasingService.get_purchase_order(tenant_id, po_id)
    if not po:
        return jsonify({'error': 'Purchase order not found'}), 404
    return jsonify({'order': po.to_dict()})


@purchasing_bp.route('/orders', methods=['POST'])
@jwt_required()
@tenant_required
def create_order():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    user_id = get_jwt_identity()
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        po = PurchasingService.create_purchase_order(
            tenant_id, request.get_json() or {}, user_id=user_id)
        return jsonify({'order': po.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@purchasing_bp.route('/orders/<po_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_order(po_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        po = PurchasingService.update_purchase_order(
            tenant_id, po_id, request.get_json() or {})
        if not po:
            return jsonify({'error': 'Purchase order not found'}), 404
        return jsonify({'order': po.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@purchasing_bp.route('/orders/<po_id>/receive', methods=['POST'])
@jwt_required()
@tenant_required
def receive_goods(po_id):
    """Receive goods for PO – auto-adjusts inventory stock."""
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    user_id = get_jwt_identity()
    err = _module_check(tenant_id)
    if err:
        return err
    data = request.get_json() or {}
    try:
        po = PurchasingService.receive_goods(
            tenant_id, po_id,
            received_items=data.get('items', []),
            user_id=user_id)
        return jsonify({
            'message': 'Goods received successfully',
            'order': po.to_dict(),
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Stats ────────────────────────────────────────────────────

@purchasing_bp.route('/stats', methods=['GET'])
@jwt_required()
@tenant_required
def purchasing_stats():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    stats = PurchasingService.get_purchasing_stats(tenant_id)
    return jsonify({'stats': stats})
