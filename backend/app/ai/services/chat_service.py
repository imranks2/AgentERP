"""Chat service — manages conversations and invokes the AI agent."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple, List

from flask import current_app

from app import db
from app.models.ai import Conversation, Message, AIInteractionLog
from app.ai.agent import ERPAgent


class ChatService:
    """Stateless service for AI chat operations."""

    @staticmethod
    def create_conversation(tenant_id: str, user_id: str, title: str = None) -> Conversation:
        convo = Conversation(tenant_id=tenant_id, user_id=user_id,
                             title=title or 'New conversation')
        db.session.add(convo)
        db.session.commit()
        return convo

    @staticmethod
    def list_conversations(tenant_id: str, user_id: str,
                           page: int = 1, per_page: int = 20) -> Tuple[List[Conversation], int]:
        q = Conversation.query.filter_by(tenant_id=tenant_id, user_id=user_id, status='active') \
            .order_by(Conversation.updated_at.desc())
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_conversation(tenant_id: str, conversation_id: str) -> Optional[Conversation]:
        return Conversation.query.filter_by(id=conversation_id, tenant_id=tenant_id).first()

    @staticmethod
    def delete_conversation(tenant_id: str, conversation_id: str) -> bool:
        convo = Conversation.query.filter_by(id=conversation_id, tenant_id=tenant_id).first()
        if not convo:
            return False
        convo.status = 'archived'
        db.session.commit()
        return True

    @staticmethod
    def send_message(tenant_id: str, user_id: str, conversation_id: str,
                     content: str, user_permissions: list = None) -> dict:
        """Process a user message through the AI agent and return the result.

        Returns dict with keys: user_message, assistant_message, agent_result
        """
        convo = Conversation.query.filter_by(id=conversation_id, tenant_id=tenant_id).first()
        if not convo:
            raise ValueError('Conversation not found')

        # 1. Persist user message
        user_msg = Message(
            conversation_id=conversation_id,
            role='user',
            content=content,
        )
        db.session.add(user_msg)
        db.session.flush()

        # 2. Build message history
        history = [m.to_dict() for m in convo.messages.order_by(Message.created_at).all()]

        # 3. Get LLM and invoke agent
        llm = current_app.config.get('AI_LLM')
        agent = ERPAgent(
            llm=llm,
            tenant_id=tenant_id,
            user_id=user_id,
            user_permissions=user_permissions or [],
        )
        result = agent.invoke(content, history)

        # 4. Persist assistant response
        assistant_msg = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=result['content'],
            tool_calls=result['tool_calls'] if result['tool_calls'] else None,
            tokens_used=result.get('tokens_in', 0) + result.get('tokens_out', 0),
            model=result.get('model'),
        )
        db.session.add(assistant_msg)

        # 5. Update conversation title (auto-generate from first message)
        if convo.title == 'New conversation' and content:
            convo.title = content[:80] + ('…' if len(content) > 80 else '')
        convo.updated_at = datetime.now(timezone.utc)

        # 6. Log AI interaction
        log = AIInteractionLog(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            action_type='chat',
            input_summary=content[:500],
            output_summary=result['content'][:500] if result['content'] else None,
            tools_used=[tc['name'] for tc in result.get('tool_calls', [])],
            latency_ms=result.get('latency_ms'),
            tokens_in=result.get('tokens_in', 0),
            tokens_out=result.get('tokens_out', 0),
            model=result.get('model'),
        )
        db.session.add(log)

        db.session.commit()

        # 7. Emit event
        try:
            from app.events import event_bus
            event_bus.emit('ai.chat.message', tenant_id=tenant_id, user_id=user_id,
                           data={'conversation_id': conversation_id,
                                 'tools_used': [tc['name'] for tc in result.get('tool_calls', [])]})
        except Exception:
            pass

        return {
            'user_message': user_msg.to_dict(),
            'assistant_message': assistant_msg.to_dict(),
            'interaction_id': log.id,
            'confidence': result.get('confidence', 0.0),
            'reasoning': result.get('reasoning'),
        }

    @staticmethod
    def one_shot_query(tenant_id: str, user_id: str, query: str,
                       user_permissions: list = None) -> dict:
        """Execute a one-shot natural language query (no conversation context)."""
        llm = current_app.config.get('AI_LLM')
        agent = ERPAgent(
            llm=llm,
            tenant_id=tenant_id,
            user_id=user_id,
            user_permissions=user_permissions or [],
        )
        result = agent.invoke(query)

        # Log it
        log = AIInteractionLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action_type='nl_query',
            input_summary=query[:500],
            output_summary=result['content'][:500] if result['content'] else None,
            tools_used=[tc['name'] for tc in result.get('tool_calls', [])],
            latency_ms=result.get('latency_ms'),
            tokens_in=result.get('tokens_in', 0),
            tokens_out=result.get('tokens_out', 0),
            model=result.get('model'),
        )
        db.session.add(log)
        db.session.commit()

        return {
            'answer': result['content'],
            'tool_calls': result.get('tool_calls', []),
            'interaction_id': log.id,
            'model': result.get('model'),
            'confidence': result.get('confidence', 0.0),
            'reasoning': result.get('reasoning'),
        }

    @staticmethod
    def submit_feedback(interaction_id: str, feedback: str) -> Optional[AIInteractionLog]:
        log = AIInteractionLog.query.get(interaction_id)
        if not log:
            return None
        log.feedback = feedback  # 'thumbs_up' or 'thumbs_down'
        db.session.commit()
        return log
