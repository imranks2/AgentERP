"""AI / Agentic Layer models – Phase 7."""
import uuid
from datetime import datetime, timezone
from app import db


def _uuid():
    return str(uuid.uuid4())


class Conversation(db.Model):
    """A chat conversation between a user and the AI assistant."""
    __tablename__ = 'conversations'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='active')  # active | archived
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    messages = db.relationship('Message', backref='conversation', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='Message.created_at')

    def to_dict(self, include_messages=False):
        d = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'title': self.title,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            d['messages'] = [m.to_dict() for m in self.messages.all()]
        return d


class Message(db.Model):
    """A single message in a conversation."""
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id', ondelete='CASCADE'),
                                nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # user | assistant | system | tool
    content = db.Column(db.Text, nullable=True)
    tool_calls = db.Column(db.JSON, nullable=True)   # list of {name, args, result}
    tool_call_id = db.Column(db.String(100), nullable=True)
    tokens_used = db.Column(db.Integer, default=0)
    model = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'tool_calls': self.tool_calls,
            'tool_call_id': self.tool_call_id,
            'tokens_used': self.tokens_used,
            'model': self.model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AIInteractionLog(db.Model):
    """Audit / training log for every AI invocation."""
    __tablename__ = 'ai_interaction_logs'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    conversation_id = db.Column(db.String(36), nullable=True)
    action_type = db.Column(db.String(30), nullable=False)  # chat | suggestion | nl_query
    input_summary = db.Column(db.Text, nullable=True)
    output_summary = db.Column(db.Text, nullable=True)
    tools_used = db.Column(db.JSON, nullable=True)
    feedback = db.Column(db.String(20), nullable=True)  # thumbs_up | thumbs_down | null
    latency_ms = db.Column(db.Integer, nullable=True)
    tokens_in = db.Column(db.Integer, default=0)
    tokens_out = db.Column(db.Integer, default=0)
    model = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'action_type': self.action_type,
            'input_summary': self.input_summary,
            'output_summary': self.output_summary,
            'tools_used': self.tools_used,
            'feedback': self.feedback,
            'latency_ms': self.latency_ms,
            'tokens_in': self.tokens_in,
            'tokens_out': self.tokens_out,
            'model': self.model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
