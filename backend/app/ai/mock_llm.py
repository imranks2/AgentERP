"""Mock LLM for development and testing without an API key.

Uses keyword matching to determine which tool to call, then returns
deterministic responses wrapping the tool output.  The agent loop
works identically regardless of real or mock LLM.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any, Dict, List, Optional

# Pattern → tool name mapping.  First match wins.
_INTENT_MAP: List[tuple] = [
    # Inventory
    (r'low.?stock|reorder|below.?reorder', 'list_low_stock', {}),
    (r'inventor(y|ies)\s+stat', 'get_inventory_stats', {}),
    (r'warehouse', 'list_warehouses', {}),
    (r'stock\s+level|stock\s+on\s+hand', 'get_stock_levels', {}),
    (r'product|item|sku', 'list_products', {}),
    # Sales
    (r'overdue.*(invoice|bill)', 'list_invoices', {'status': 'overdue'}),
    (r'unpaid.*(invoice|bill)', 'list_invoices', {'status': 'sent'}),
    (r'paid.*(invoice|bill)', 'list_invoices', {'status': 'paid'}),
    (r'invoice|bill', 'list_invoices', {}),
    (r'quotation|quote', 'list_quotations', {}),
    (r'payment', 'list_payments', {}),
    (r'customer|client', 'list_customers', {}),
    (r'sales?\s+stat|revenue', 'get_sales_stats', {}),
    # Purchasing
    (r'supplier|vendor', 'list_suppliers', {}),
    (r'purchase.?order|PO\b', 'list_purchase_orders', {}),
    (r'purchas\w*\s+stat', 'get_purchasing_stats', {}),
    # Organisation
    (r'org(anisation|anization)?\s+tree|org\s+chart', 'get_org_tree', {}),
    (r'department|branch|business.?unit|org.?unit', 'list_org_units', {}),
    # Users
    (r'user|team.?member', 'list_users', {}),
    # Accounting
    (r'trial.?balance', 'get_trial_balance', {}),
    (r'profit.*(loss|income)|income.?statement|p\s*&\s*l', 'get_profit_loss', {}),
    (r'balance.?sheet', 'get_balance_sheet', {}),
    (r'journal.?entr', 'list_journal_entries', {}),
    (r'chart.?of.?account|account.?list|ledger', 'list_accounts', {}),
    (r'account\w*\s+stat', 'get_accounting_stats', {}),
    # CRM
    (r'pipeline|funnel', 'get_pipeline_stats', {}),
    (r'opportunit', 'list_opportunities', {}),
    (r'lead', 'list_leads', {}),
    # HR
    (r'leave.?request|time.?off|vacation', 'list_leave_requests', {}),
    (r'employee|staff|personnel', 'list_employees', {}),
    (r'hr\s+stat|headcount', 'get_hr_stats', {}),
]


class MockLLM:
    """Deterministic mock that maps user messages to tool calls."""

    model_name = 'mock'

    def decide(self, user_message: str, available_tools: List[str]) -> Optional[Dict[str, Any]]:
        """Return a tool call dict or None if no match found.

        Returns ``{'name': ..., 'arguments': {...}, 'confidence': float, 'reasoning': str}``
        matching the OpenAI tool_calls structure with added explainability.
        """
        msg = user_message.lower()
        for pattern, tool_name, extra_args in _INTENT_MAP:
            m = re.search(pattern, msg)
            if m and tool_name in available_tools:
                # Compute confidence from match quality
                match_ratio = len(m.group()) / max(len(msg), 1)
                confidence = min(0.5 + match_ratio * 2, 0.99)

                # Merge pattern-derived args with any heuristic extras
                args = dict(extra_args)
                # Try to extract a search term
                search_match = re.search(r'(?:for|named?|called?|search)\s+"?([^"]+)"?', msg)
                if search_match and 'search' in self._param_keys(tool_name):
                    args['search'] = search_match.group(1).strip()
                return {
                    'id': f'call_{uuid.uuid4().hex[:12]}',
                    'name': tool_name,
                    'arguments': args,
                    'confidence': round(confidence, 2),
                    'reasoning': f'Matched pattern "{pattern}" against user query. '
                                 f'Tool "{tool_name}" selected with {round(confidence * 100)}% confidence.',
                }
        return None

    def format_response(self, user_message: str, tool_name: Optional[str],
                        tool_result: Any) -> str:
        """Create a human-friendly response from the tool output."""
        if tool_result is None:
            return self._fallback_response(user_message)

        try:
            if isinstance(tool_result, dict):
                return self._format_dict(tool_name, tool_result)
            if isinstance(tool_result, list):
                return self._format_list(tool_name, tool_result)
            return str(tool_result)
        except Exception:
            return f"I ran **{tool_name}** but couldn't format the result. Raw data:\n```json\n{json.dumps(tool_result, default=str)[:1000]}\n```"

    # ─── helpers ──────────────────────────────────────────────
    @staticmethod
    def _param_keys(tool_name: str) -> set:
        from app.ai.tools.registry import registry
        t = registry.get(tool_name)
        if t and t.parameters:
            return set(t.parameters.get('properties', {}).keys())
        return set()

    @staticmethod
    def _format_dict(tool_name: str, data: dict) -> str:
        # Common patterns: {items_key: [...], total: N}
        for key in ('products', 'customers', 'invoices', 'quotations',
                     'payments', 'suppliers', 'purchase_orders', 'users'):
            if key in data:
                items = data[key]
                total = data.get('total', len(items))
                if not items:
                    return f"No {key.replace('_', ' ')} found."
                lines = [f"Found **{total}** {key.replace('_', ' ')}:\n"]
                for i, item in enumerate(items[:10], 1):
                    name = item.get('name') or item.get('full_name') or item.get('number') or item.get('email') or str(item.get('id', ''))[:8]
                    status = item.get('status', '')
                    extra = f" — {status}" if status else ''
                    lines.append(f"{i}. **{name}**{extra}")
                if total > 10:
                    lines.append(f"\n_…and {total - 10} more._")
                return '\n'.join(lines)

        # Stats-like dict
        lines = [f"**{tool_name.replace('_', ' ').title()}**:\n"]
        for k, v in data.items():
            label = k.replace('_', ' ').title()
            lines.append(f"- {label}: **{v}**")
        return '\n'.join(lines)

    @staticmethod
    def _format_list(tool_name: str, data: list) -> str:
        if not data:
            return "No results found."
        lines = [f"Found **{len(data)}** results:\n"]
        for i, item in enumerate(data[:10], 1):
            if isinstance(item, dict):
                name = item.get('name') or item.get('full_name') or str(item.get('id', ''))[:8]
                lines.append(f"{i}. **{name}**")
            else:
                lines.append(f"{i}. {item}")
        return '\n'.join(lines)

    @staticmethod
    def _fallback_response(user_message: str) -> str:
        return (
            "I'm your ERP assistant. I can help you with:\n\n"
            "- **Inventory**: products, stock levels, warehouses, low stock alerts\n"
            "- **Sales**: customers, quotations, invoices, overdue invoices, payments\n"
            "- **Purchasing**: suppliers, purchase orders, receiving goods\n"
            "- **Organisation**: org tree, departments, branches\n"
            "- **Users**: team members, roles\n\n"
            "Try asking something like *\"show me overdue invoices\"* or *\"list low stock products\"*."
        )
