"""Tool auto-discovery for AI agent."""
from app.ai.tools.registry import registry

# Import all tool modules so their @erp_tool decorators run at import time
from app.ai.tools import (  # noqa: F401
    inventory_tools,
    sales_tools,
    purchasing_tools,
    organisation_tools,
    user_tools,
    accounting_tools,
    crm_tools,
    hr_tools,
)


def discover_tools():
    """Return the fully populated ToolRegistry (import side-effects do the work)."""
    return registry
