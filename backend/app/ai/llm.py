"""LLM provider factory — returns real OpenAI or mock LLM based on config."""
from __future__ import annotations

from app.ai.mock_llm import MockLLM


def should_use_mock(app_config: dict) -> bool:
    mode = app_config.get('AI_MOCK_MODE', 'auto')
    if mode == 'always':
        return True
    if mode == 'never':
        return False
    # auto: use mock if no API key is set
    return not app_config.get('OPENAI_API_KEY')


def get_llm(app_config: dict):
    """Return an LLM instance.  Falls back to MockLLM when no API key."""
    if should_use_mock(app_config):
        return MockLLM()

    # Real OpenAI integration
    try:
        from openai import OpenAI
        return OpenAI(api_key=app_config['OPENAI_API_KEY'])
    except Exception:
        return MockLLM()
