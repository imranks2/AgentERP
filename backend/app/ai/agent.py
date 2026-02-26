"""ERP Agent — the core AI agent that processes user messages.

Supports both real OpenAI (tool-calling) and the mock LLM.
The agent loop:
  1. Analyse user message
  2. Optionally call one or more tools
  3. Compose a final assistant response
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Optional

from app.ai.mock_llm import MockLLM
from app.ai.tools.registry import registry


SYSTEM_PROMPT = """You are an AI assistant for AgentERP, an enterprise resource planning platform.
You have access to tools that can query and manage business data.
Always respond concisely and helpfully.  Format data in markdown when appropriate.
When presenting lists, use numbered lists. When presenting statistics, use bold labels.
Never fabricate data — always use the provided tools to fetch real information.
The current tenant and user context is provided automatically — do not ask for tenant or user IDs.
"""


class ERPAgent:
    """Stateless agent that processes a single turn (message → response)."""

    def __init__(self, llm, tenant_id: str, user_id: str, user_permissions: List[str]):
        self.llm = llm
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_permissions = user_permissions
        self.is_mock = isinstance(llm, MockLLM)
        # Filter tools by permission
        self._tools = registry.tools_for_permissions(user_permissions)
        self._tool_names = {t.name for t in self._tools}

    def invoke(self, user_message: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process a user message and return an agent result.

        Returns:
            {
              'content': str,         # assistant response text
              'tool_calls': list,     # [{name, arguments, result}, ...]
              'model': str,
              'tokens_in': int,
              'tokens_out': int,
              'latency_ms': int,
            }
        """
        start = time.time()
        tool_calls = []
        confidence = 0.0
        reasoning = None

        if self.is_mock:
            content, tool_calls, confidence, reasoning = self._invoke_mock(user_message)
            model = 'mock'
            tokens_in = tokens_out = 0
        else:
            content, tool_calls, model, tokens_in, tokens_out = self._invoke_openai(
                user_message, history or []
            )
            confidence = 0.85  # default for real LLM
            reasoning = 'Processed via OpenAI API with tool-calling capability.'

        latency_ms = int((time.time() - start) * 1000)

        return {
            'content': content,
            'tool_calls': tool_calls,
            'model': model,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'latency_ms': latency_ms,
            'confidence': confidence,
            'reasoning': reasoning,
        }

    # ─── Mock path ────────────────────────────────────────────
    def _invoke_mock(self, user_message: str):
        tool_calls = []
        confidence = 0.0
        reasoning = None
        decision = self.llm.decide(user_message, self._tool_names)

        if decision:
            tool_name = decision['name']
            tool_args = decision.get('arguments', {})
            confidence = decision.get('confidence', 0.5)
            reasoning = decision.get('reasoning')
            tool_def = registry.get(tool_name)

            result = None
            if tool_def:
                try:
                    result = tool_def.fn(self.tenant_id, **tool_args)
                except Exception as e:
                    result = {'error': str(e)}

            tool_calls.append({
                'id': decision.get('id', str(uuid.uuid4())),
                'name': tool_name,
                'arguments': tool_args,
                'result': result,
            })
            content = self.llm.format_response(user_message, tool_name, result)
        else:
            content = self.llm.format_response(user_message, None, None)
            reasoning = 'No matching intent pattern found for the query.'

        return content, tool_calls, confidence, reasoning

    # ─── OpenAI path ──────────────────────────────────────────
    def _invoke_openai(self, user_message: str, history: list):
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        for h in history[-20:]:  # keep last 20 messages
            messages.append({'role': h['role'], 'content': h.get('content', '')})
        messages.append({'role': 'user', 'content': user_message})

        functions = registry.to_openai_functions(self._tools)
        tool_calls = []
        total_in = total_out = 0
        model_name = 'unknown'

        try:
            # Up to 3 rounds of tool calls
            for _ in range(3):
                kwargs = {'model': self.llm._model_name if hasattr(self.llm, '_model_name') else 'gpt-4o',
                          'messages': messages}
                if functions:
                    kwargs['tools'] = functions

                response = self.llm.chat.completions.create(**kwargs)
                choice = response.choices[0]
                model_name = response.model
                total_in += response.usage.prompt_tokens if response.usage else 0
                total_out += response.usage.completion_tokens if response.usage else 0

                if choice.finish_reason == 'tool_calls' and choice.message.tool_calls:
                    # Execute each tool
                    messages.append(choice.message.model_dump())
                    for tc in choice.message.tool_calls:
                        fn_name = tc.function.name
                        fn_args = json.loads(tc.function.arguments)
                        tool_def = registry.get(fn_name)
                        result = None
                        if tool_def:
                            try:
                                result = tool_def.fn(self.tenant_id, **fn_args)
                            except Exception as e:
                                result = {'error': str(e)}
                        tool_calls.append({
                            'id': tc.id,
                            'name': fn_name,
                            'arguments': fn_args,
                            'result': result,
                        })
                        messages.append({
                            'role': 'tool',
                            'tool_call_id': tc.id,
                            'content': json.dumps(result, default=str),
                        })
                else:
                    # Done — return final text
                    return choice.message.content or '', tool_calls, model_name, total_in, total_out
        except Exception as e:
            return f"Sorry, I encountered an error: {e}", tool_calls, model_name, total_in, total_out

        return 'I completed the requested actions.', tool_calls, model_name, total_in, total_out
