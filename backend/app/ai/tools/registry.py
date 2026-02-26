"""ERP Tool Registry — Phase 7.

Provides the @erp_tool decorator and a global ToolRegistry that catalogues
every action the AI agent can perform.  Each tool wraps an existing service
method to guarantee tenant isolation and permission enforcement.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDefinition:
    """Metadata for a registered ERP tool."""
    name: str
    description: str
    module: str                    # e.g. 'sales', 'inventory'
    permissions: List[str]         # required permissions to use this tool
    parameters: Dict[str, Any]     # JSON-Schema-like parameter descriptions
    fn: Callable                   # the wrapped function


class ToolRegistry:
    """Singleton registry of all ERP tools available to the AI agent."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    # ------------------------------------------------------------------
    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def all_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def tools_for_permissions(self, user_permissions: List[str]) -> List[ToolDefinition]:
        """Return only tools the user is allowed to invoke."""
        result = []
        for t in self._tools.values():
            if not t.permissions:
                result.append(t)
                continue
            if any(p in user_permissions for p in t.permissions):
                result.append(t)
        return result

    def to_openai_functions(self, tools: Optional[List[ToolDefinition]] = None):
        """Convert tools to OpenAI function-calling schema."""
        tools = tools or self.all_tools()
        funcs = []
        for t in tools:
            funcs.append({
                'type': 'function',
                'function': {
                    'name': t.name,
                    'description': t.description,
                    'parameters': t.parameters or {'type': 'object', 'properties': {}},
                },
            })
        return funcs

    def __len__(self):
        return len(self._tools)


# Global singleton
registry = ToolRegistry()


def erp_tool(
    name: str,
    description: str,
    module: str = 'general',
    permissions: Optional[List[str]] = None,
    parameters: Optional[Dict[str, Any]] = None,
):
    """Decorator to register a function as an ERP tool.

    The decorated function **must** accept ``tenant_id`` as its first
    positional argument so tenant isolation is always enforced.
    """
    def decorator(fn: Callable):
        tool = ToolDefinition(
            name=name,
            description=description,
            module=module,
            permissions=permissions or [],
            parameters=parameters or {'type': 'object', 'properties': {}},
            fn=fn,
        )
        registry.register(tool)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper._tool_def = tool
        return wrapper

    return decorator
