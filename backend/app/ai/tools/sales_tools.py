"""Sales tools for the AI agent."""
from app.ai.tools.registry import erp_tool
from app.services.sales_service import SalesService


@erp_tool(
    name='list_customers',
    description='List customers with optional search filter.',
    module='sales',
    permissions=['sales.view'],
    parameters={
        'type': 'object',
        'properties': {
            'search': {'type': 'string', 'description': 'Search by customer name or email'},
        },
    },
)
def list_customers(tenant_id, search=None):
    customers, total = SalesService.list_customers(tenant_id, search=search, page=1, per_page=20)
    return {'customers': [c.to_dict() for c in customers], 'total': total}


@erp_tool(
    name='list_quotations',
    description='List sales quotations with optional status and customer filters.',
    module='sales',
    permissions=['sales.view'],
    parameters={
        'type': 'object',
        'properties': {
            'status': {'type': 'string', 'enum': ['draft', 'sent', 'accepted', 'rejected', 'expired', 'converted']},
            'customer_id': {'type': 'string'},
        },
    },
)
def list_quotations(tenant_id, status=None, customer_id=None):
    quotes, total = SalesService.list_quotations(tenant_id, status=status, customer_id=customer_id, page=1, per_page=20)
    return {'quotations': [q.to_dict() for q in quotes], 'total': total}


@erp_tool(
    name='list_invoices',
    description='List invoices with optional status filter. Use status="overdue" to find overdue invoices.',
    module='sales',
    permissions=['sales.view'],
    parameters={
        'type': 'object',
        'properties': {
            'status': {'type': 'string', 'enum': ['draft', 'sent', 'partial', 'paid', 'overdue', 'cancelled']},
            'customer_id': {'type': 'string'},
        },
    },
)
def list_invoices(tenant_id, status=None, customer_id=None):
    invoices, total = SalesService.list_invoices(tenant_id, status=status, customer_id=customer_id, page=1, per_page=20)
    return {'invoices': [i.to_dict() for i in invoices], 'total': total}


@erp_tool(
    name='get_sales_stats',
    description='Get sales statistics: total revenue, outstanding amount, invoice counts, etc.',
    module='sales',
    permissions=['sales.view'],
    parameters={'type': 'object', 'properties': {}},
)
def get_sales_stats(tenant_id):
    return SalesService.get_sales_stats(tenant_id)


@erp_tool(
    name='list_payments',
    description='List payment records, optionally filtered by invoice.',
    module='sales',
    permissions=['sales.view'],
    parameters={
        'type': 'object',
        'properties': {
            'invoice_id': {'type': 'string', 'description': 'Filter by invoice ID'},
        },
    },
)
def list_payments(tenant_id, invoice_id=None):
    payments, total = SalesService.list_payments(tenant_id, invoice_id=invoice_id, page=1, per_page=20)
    return {'payments': [p.to_dict() for p in payments], 'total': total}
