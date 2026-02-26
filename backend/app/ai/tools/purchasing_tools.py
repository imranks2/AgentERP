"""Purchasing tools for the AI agent."""
from app.ai.tools.registry import erp_tool
from app.services.purchasing_service import PurchasingService


@erp_tool(
    name='list_suppliers',
    description='List suppliers with optional search filter.',
    module='purchasing',
    permissions=['purchasing.view'],
    parameters={
        'type': 'object',
        'properties': {
            'search': {'type': 'string', 'description': 'Search by supplier name or contact'},
        },
    },
)
def list_suppliers(tenant_id, search=None):
    suppliers, total = PurchasingService.list_suppliers(tenant_id, search=search, page=1, per_page=20)
    return {'suppliers': [s.to_dict() for s in suppliers], 'total': total}


@erp_tool(
    name='list_purchase_orders',
    description='List purchase orders with optional status and supplier filters.',
    module='purchasing',
    permissions=['purchasing.view'],
    parameters={
        'type': 'object',
        'properties': {
            'status': {'type': 'string', 'enum': ['draft', 'sent', 'partial', 'received', 'cancelled']},
            'supplier_id': {'type': 'string'},
        },
    },
)
def list_purchase_orders(tenant_id, status=None, supplier_id=None):
    orders, total = PurchasingService.list_purchase_orders(
        tenant_id, status=status, supplier_id=supplier_id, page=1, per_page=20,
    )
    return {'purchase_orders': [o.to_dict() for o in orders], 'total': total}


@erp_tool(
    name='get_purchasing_stats',
    description='Get purchasing statistics: total orders, pending receipts, total value, etc.',
    module='purchasing',
    permissions=['purchasing.view'],
    parameters={'type': 'object', 'properties': {}},
)
def get_purchasing_stats(tenant_id):
    return PurchasingService.get_purchasing_stats(tenant_id)
