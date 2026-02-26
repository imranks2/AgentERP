"""Inventory tools for the AI agent."""
from app.ai.tools.registry import erp_tool
from app.services.inventory_service import InventoryService


@erp_tool(
    name='list_products',
    description='List products in the inventory with optional filters. Returns a list of product dicts.',
    module='inventory',
    permissions=['inventory.view'],
    parameters={
        'type': 'object',
        'properties': {
            'search': {'type': 'string', 'description': 'Search by product name or SKU'},
            'category_id': {'type': 'string', 'description': 'Filter by category ID'},
            'product_type': {'type': 'string', 'enum': ['goods', 'service', 'consumable']},
        },
    },
)
def list_products(tenant_id, search=None, category_id=None, product_type=None):
    products, total = InventoryService.list_products(
        tenant_id, category_id=category_id, search=search,
        product_type=product_type, page=1, per_page=20,
    )
    return {'products': [p.to_dict() for p in products], 'total': total}


@erp_tool(
    name='get_product',
    description='Get details of a specific product by its ID.',
    module='inventory',
    permissions=['inventory.view'],
    parameters={
        'type': 'object',
        'properties': {
            'product_id': {'type': 'string', 'description': 'The product ID'},
        },
        'required': ['product_id'],
    },
)
def get_product(tenant_id, product_id=None):
    p = InventoryService.get_product(tenant_id, product_id)
    return p.to_dict() if p else {'error': 'Product not found'}


@erp_tool(
    name='get_stock_levels',
    description='Get current stock levels, optionally filtered by product or warehouse.',
    module='inventory',
    permissions=['inventory.view'],
    parameters={
        'type': 'object',
        'properties': {
            'product_id': {'type': 'string', 'description': 'Filter by product ID'},
            'warehouse_id': {'type': 'string', 'description': 'Filter by warehouse ID'},
        },
    },
)
def get_stock_levels(tenant_id, product_id=None, warehouse_id=None):
    entries = InventoryService.get_stock(tenant_id, product_id=product_id, warehouse_id=warehouse_id)
    return [{'product_id': e.product_id, 'warehouse_id': e.warehouse_id,
             'quantity': e.quantity, 'product_name': e.product.name if e.product else None}
            for e in entries]


@erp_tool(
    name='list_low_stock',
    description='List products that are at or below their reorder point (low stock).',
    module='inventory',
    permissions=['inventory.view'],
    parameters={'type': 'object', 'properties': {}},
)
def list_low_stock(tenant_id):
    stats = InventoryService.get_inventory_stats(tenant_id)
    return {'low_stock_count': stats.get('low_stock', 0), 'stats': stats}


@erp_tool(
    name='get_inventory_stats',
    description='Get inventory statistics: total products, total value, low stock count, etc.',
    module='inventory',
    permissions=['inventory.view'],
    parameters={'type': 'object', 'properties': {}},
)
def get_inventory_stats(tenant_id):
    return InventoryService.get_inventory_stats(tenant_id)


@erp_tool(
    name='list_warehouses',
    description='List all warehouses for the tenant.',
    module='inventory',
    permissions=['inventory.view'],
    parameters={'type': 'object', 'properties': {}},
)
def list_warehouses(tenant_id):
    whs = InventoryService.list_warehouses(tenant_id)
    return [w.to_dict() for w in whs]
