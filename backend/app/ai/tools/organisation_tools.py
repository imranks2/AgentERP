"""Organisation tools for the AI agent."""
from app.ai.tools.registry import erp_tool
from app.services.organisation_service import OrganisationService


@erp_tool(
    name='get_org_tree',
    description='Get the full organisation tree for the tenant.',
    module='organisation',
    permissions=['org.view'],
    parameters={'type': 'object', 'properties': {}},
)
def get_org_tree(tenant_id):
    return OrganisationService.get_tree(tenant_id)


@erp_tool(
    name='list_org_units',
    description='List organisation units with optional filters.',
    module='organisation',
    permissions=['org.view'],
    parameters={
        'type': 'object',
        'properties': {
            'unit_type': {'type': 'string', 'description': 'Filter by unit type (e.g. department, branch)'},
            'search': {'type': 'string', 'description': 'Search by unit name'},
        },
    },
)
def list_org_units(tenant_id, unit_type=None, search=None):
    units = OrganisationService.list_units(tenant_id, unit_type=unit_type, search=search)
    return [u.to_dict() for u in units]
