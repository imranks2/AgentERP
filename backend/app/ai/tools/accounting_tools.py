"""AI tools for the Accounting module."""
from app.ai.tools.registry import erp_tool


@erp_tool(
    name='list_accounts',
    description='List chart of accounts entries, optionally filtered by type.',
    module='accounting',
    permissions=['accounting.view'],
    parameters={
        'account_type': {'type': 'string', 'description': 'Filter by type: asset, liability, equity, revenue, expense'},
        'search': {'type': 'string', 'description': 'Search by name or code'},
    },
)
def list_accounts(tenant_id, account_type=None, search=None):
    from app.services.accounting_service import AccountingService
    accts, total = AccountingService.list_accounts(
        tenant_id, account_type=account_type, search=search, per_page=20)
    return {'accounts': [a.to_dict() for a in accts], 'total': total}


@erp_tool(
    name='list_journal_entries',
    description='List journal entries, optionally filtered by status.',
    module='accounting',
    permissions=['accounting.view'],
    parameters={
        'status': {'type': 'string', 'description': 'Filter: draft, posted, reversed'},
    },
)
def list_journal_entries(tenant_id, status=None):
    from app.services.accounting_service import AccountingService
    entries, total = AccountingService.list_journal_entries(
        tenant_id, status=status, per_page=20)
    return {'entries': [e.to_dict() for e in entries], 'total': total}


@erp_tool(
    name='get_trial_balance',
    description='Get trial balance report showing all account balances.',
    module='accounting',
    permissions=['accounting.view'],
    parameters={},
)
def get_trial_balance(tenant_id):
    from app.services.accounting_service import AccountingService
    return {'trial_balance': AccountingService.trial_balance(tenant_id)}


@erp_tool(
    name='get_profit_loss',
    description='Get profit and loss (income statement) report.',
    module='accounting',
    permissions=['accounting.view'],
    parameters={},
)
def get_profit_loss(tenant_id):
    from app.services.accounting_service import AccountingService
    return AccountingService.profit_and_loss(tenant_id)


@erp_tool(
    name='get_balance_sheet',
    description='Get balance sheet report showing assets, liabilities are equity.',
    module='accounting',
    permissions=['accounting.view'],
    parameters={},
)
def get_balance_sheet(tenant_id):
    from app.services.accounting_service import AccountingService
    return AccountingService.balance_sheet(tenant_id)


@erp_tool(
    name='get_accounting_stats',
    description='Get accounting statistics like total accounts and journal entries.',
    module='accounting',
    permissions=['accounting.view'],
    parameters={},
)
def get_accounting_stats(tenant_id):
    from app.services.accounting_service import AccountingService
    return AccountingService.get_stats(tenant_id)
