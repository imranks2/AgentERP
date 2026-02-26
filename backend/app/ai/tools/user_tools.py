"""User tools for the AI agent."""
from app.ai.tools.registry import erp_tool
from app.services.user_service import UserService


@erp_tool(
    name='list_users',
    description='List users in the tenant with optional search and role filters.',
    module='users',
    permissions=['users.view'],
    parameters={
        'type': 'object',
        'properties': {
            'search': {'type': 'string', 'description': 'Search by name or email'},
            'role_slug': {'type': 'string', 'description': 'Filter by role slug'},
        },
    },
)
def list_users(tenant_id, search=None, role_slug=None):
    users, total = UserService.list_users(tenant_id, search=search, role_slug=role_slug, page=1, per_page=20)
    return {'users': [u.to_dict() for u in users], 'total': total}
