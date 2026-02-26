"""AI tools for the HR module."""
from app.ai.tools.registry import erp_tool


@erp_tool(
    name='list_employees',
    description='List HR employees, optionally filtered by status or department.',
    module='hr',
    permissions=['hr.view'],
    parameters={
        'status': {'type': 'string', 'description': 'Filter: active, on_leave, terminated'},
        'search': {'type': 'string', 'description': 'Search by name, number, or email'},
    },
)
def list_employees(tenant_id, status=None, search=None):
    from app.services.hr_service import HRService
    emps, total = HRService.list_employees(
        tenant_id, status=status, search=search, per_page=20)
    return {'employees': [e.to_dict() for e in emps], 'total': total}


@erp_tool(
    name='list_leave_requests',
    description='List employee leave requests, optionally filtered by status.',
    module='hr',
    permissions=['hr.view'],
    parameters={
        'status': {'type': 'string', 'description': 'Filter: pending, approved, rejected, cancelled'},
    },
)
def list_leave_requests(tenant_id, status=None):
    from app.services.hr_service import HRService
    reqs, total = HRService.list_leave_requests(
        tenant_id, status=status, per_page=20)
    return {'leave_requests': [r.to_dict() for r in reqs], 'total': total}


@erp_tool(
    name='get_hr_stats',
    description='Get HR statistics: total employees, active, on leave, pending requests.',
    module='hr',
    permissions=['hr.view'],
    parameters={},
)
def get_hr_stats(tenant_id):
    from app.services.hr_service import HRService
    return HRService.get_stats(tenant_id)
