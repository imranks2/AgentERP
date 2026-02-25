"""Inventory module API routes – Products, Categories, Warehouses, Stock."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.utils.decorators import tenant_required
from app.services.inventory_service import InventoryService

inventory_bp = Blueprint('inventory', __name__)


def _module_check(tenant_id):
    """Verify inventory module is enabled for tenant."""
    from app.services.module_service import ModuleService
    if not ModuleService.is_module_enabled(tenant_id, 'inventory'):
        return jsonify({'error': 'Inventory module not enabled'}), 403
    return None


# ── Categories ───────────────────────────────────────────────

@inventory_bp.route('/categories', methods=['GET'])
@jwt_required()
@tenant_required
def list_categories():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    cats = InventoryService.list_categories(tenant_id)
    return jsonify({'categories': [c.to_dict() for c in cats]})


@inventory_bp.route('/categories', methods=['POST'])
@jwt_required()
@tenant_required
def create_category():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        cat = InventoryService.create_category(tenant_id, request.get_json() or {})
        return jsonify({'category': cat.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@inventory_bp.route('/categories/<cat_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_category(cat_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        cat = InventoryService.update_category(tenant_id, cat_id, request.get_json() or {})
        if not cat:
            return jsonify({'error': 'Category not found'}), 404
        return jsonify({'category': cat.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@inventory_bp.route('/categories/<cat_id>', methods=['DELETE'])
@jwt_required()
@tenant_required
def delete_category(cat_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        InventoryService.delete_category(tenant_id, cat_id)
        return jsonify({'message': 'Category deleted'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Products ─────────────────────────────────────────────────

@inventory_bp.route('/products', methods=['GET'])
@jwt_required()
@tenant_required
def list_products():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    products, total = InventoryService.list_products(
        tenant_id,
        search=request.args.get('search'),
        category_id=request.args.get('category_id'),
        product_type=request.args.get('product_type'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify({
        'products': [p.to_dict() for p in products],
        'total': total,
        'page': int(request.args.get('page', 1)),
        'per_page': int(request.args.get('per_page', 50)),
    })


@inventory_bp.route('/products/<product_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_product(product_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    product = InventoryService.get_product(tenant_id, product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'product': product.to_dict()})


@inventory_bp.route('/products', methods=['POST'])
@jwt_required()
@tenant_required
def create_product():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        product = InventoryService.create_product(tenant_id, request.get_json() or {})
        return jsonify({'product': product.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@inventory_bp.route('/products/<product_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_product(product_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        product = InventoryService.update_product(tenant_id, product_id, request.get_json() or {})
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify({'product': product.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@inventory_bp.route('/products/<product_id>', methods=['DELETE'])
@jwt_required()
@tenant_required
def delete_product(product_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        InventoryService.delete_product(tenant_id, product_id)
        return jsonify({'message': 'Product deleted'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Warehouses ───────────────────────────────────────────────

@inventory_bp.route('/warehouses', methods=['GET'])
@jwt_required()
@tenant_required
def list_warehouses():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    warehouses = InventoryService.list_warehouses(tenant_id)
    return jsonify({'warehouses': [w.to_dict() for w in warehouses]})


@inventory_bp.route('/warehouses', methods=['POST'])
@jwt_required()
@tenant_required
def create_warehouse():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        wh = InventoryService.create_warehouse(tenant_id, request.get_json() or {})
        return jsonify({'warehouse': wh.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@inventory_bp.route('/warehouses/<wh_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_warehouse(wh_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        wh = InventoryService.update_warehouse(tenant_id, wh_id, request.get_json() or {})
        if not wh:
            return jsonify({'error': 'Warehouse not found'}), 404
        return jsonify({'warehouse': wh.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Stock ────────────────────────────────────────────────────

@inventory_bp.route('/stock', methods=['GET'])
@jwt_required()
@tenant_required
def get_stock():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    stock = InventoryService.get_stock(
        tenant_id,
        product_id=request.args.get('product_id'),
        warehouse_id=request.args.get('warehouse_id'),
    )
    return jsonify({'stock': [s.to_dict() for s in stock]})


@inventory_bp.route('/stock/adjust', methods=['POST'])
@jwt_required()
@tenant_required
def adjust_stock():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    user_id = get_jwt_identity()
    err = _module_check(tenant_id)
    if err:
        return err
    data = request.get_json() or {}
    try:
        entry, movement = InventoryService.adjust_stock(
            tenant_id,
            product_id=data.get('product_id'),
            warehouse_id=data.get('warehouse_id'),
            quantity=data.get('quantity', 0),
            movement_type=data.get('movement_type', 'adjustment'),
            reference_type=data.get('reference_type'),
            reference_id=data.get('reference_id'),
            notes=data.get('notes'),
            user_id=user_id,
        )
        return jsonify({
            'stock_entry': entry.to_dict(),
            'movement': movement.to_dict(),
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@inventory_bp.route('/stock/movements', methods=['GET'])
@jwt_required()
@tenant_required
def list_movements():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    movements, total = InventoryService.get_movements(
        tenant_id,
        product_id=request.args.get('product_id'),
        warehouse_id=request.args.get('warehouse_id'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify({
        'movements': [m.to_dict() for m in movements],
        'total': total,
    })


@inventory_bp.route('/stats', methods=['GET'])
@jwt_required()
@tenant_required
def inventory_stats():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    stats = InventoryService.get_inventory_stats(tenant_id)
    return jsonify({'stats': stats})
