"""Persistent event storage and notification models."""
import uuid
from datetime import datetime, timezone
from app import db


class EventLog(db.Model):
    """Persistent store for all domain events (enables replay & history)."""
    __tablename__ = 'event_logs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = db.Column(db.String(100), nullable=False, index=True)
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey('tenants.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    )
    data = db.Column(db.JSON, default=dict)
    source = db.Column(db.String(50), default='api')
    correlation_id = db.Column(db.String(36), nullable=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'data': self.data,
            'source': self.source,
            'correlation_id': self.correlation_id,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<EventLog {self.event_type} {self.id[:8]}>'


class Notification(db.Model):
    """Per-user notification created by event handlers."""
    __tablename__ = 'notifications'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    event_type = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(500), nullable=True)
    data = db.Column(db.JSON, default=dict)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user = db.relationship(
        'User',
        backref=db.backref('notifications', cascade='all, delete-orphan', passive_deletes=True),
        lazy='select',
    )

    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Notification {self.title[:30]} read={self.is_read}>'
