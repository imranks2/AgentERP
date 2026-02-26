"""AI & Agentic Layer — Phase 7.

Provides chat-based AI assistant, tool-calling agent, and natural language
query capabilities.  Works in mock mode (no API key) for development.
"""
from app.ai.llm import get_llm, should_use_mock


def init_ai(app):
    """Initialise the AI subsystem — load tools, configure LLM provider."""
    from app.ai.tools import discover_tools

    tools = discover_tools()
    llm = get_llm(app.config)
    app.config['AI_LLM'] = llm
    app.config['AI_TOOLS'] = tools
    app.logger.info(
        'AI layer initialised: %d tools, mock=%s',
        len(tools), should_use_mock(app.config),
    )
