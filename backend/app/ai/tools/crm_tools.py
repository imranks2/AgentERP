"""AI tools for the CRM module."""
from app.ai.tools.registry import erp_tool


@erp_tool(
    name='list_leads',
    description='List CRM leads, optionally filtered by status or source.',
    module='crm',
    permissions=['crm.view'],
    parameters={
        'status': {'type': 'string', 'description': 'Filter: new, contacted, qualified, converted, lost'},
        'source': {'type': 'string', 'description': 'Filter: web, referral, campaign, other'},
        'search': {'type': 'string', 'description': 'Search by name, email, or company'},
    },
)
def list_leads(tenant_id, status=None, source=None, search=None):
    from app.services.crm_service import CRMService
    leads, total = CRMService.list_leads(
        tenant_id, status=status, source=source, search=search, per_page=20)
    return {'leads': [l.to_dict() for l in leads], 'total': total}


@erp_tool(
    name='list_opportunities',
    description='List sales pipeline opportunities, optionally filtered by stage.',
    module='crm',
    permissions=['crm.view'],
    parameters={
        'stage': {'type': 'string', 'description': 'Filter: prospecting, proposal, negotiation, won, lost'},
        'search': {'type': 'string', 'description': 'Search by title'},
    },
)
def list_opportunities(tenant_id, stage=None, search=None):
    from app.services.crm_service import CRMService
    opps, total = CRMService.list_opportunities(
        tenant_id, stage=stage, search=search, per_page=20)
    return {'opportunities': [o.to_dict() for o in opps], 'total': total}


@erp_tool(
    name='get_pipeline_stats',
    description='Get CRM pipeline statistics including stage counts and total value.',
    module='crm',
    permissions=['crm.view'],
    parameters={},
)
def get_pipeline_stats(tenant_id):
    from app.services.crm_service import CRMService
    return CRMService.pipeline_stats(tenant_id)
