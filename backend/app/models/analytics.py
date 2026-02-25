"""Analytics event model for AI training data collection."""
import uuid
from datetime import datetime, timezone
from app import db


class AnalyticsEvent(db.Model):
    """Captures user interactions for AI training pipeline.

    Every API call and frontend event is logged (with tenant consent)
    to build training data for the AI/agentic layer.

    Events are anonymised and stored separately. They power:
    - Smart defaults and recommendations
    - Anomaly detection
    - Natural language search improvements
    - Autonomous agent training
    """
    __tablename__ = 'analytics_events'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey('tenants.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    user_id = db.Column(db.String(36), nullable=True, index=True)
    session_id = db.Column(db.String(100), nullable=True)

    # Event classification
    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_category = db.Column(db.String(50), nullable=False, default='general')
    event_action = db.Column(db.String(100), nullable=False)

    # Context
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.String(36), nullable=True)
    endpoint = db.Column(db.String(255), nullable=True)
    method = db.Column(db.String(10), nullable=True)
    status_code = db.Column(db.Integer, nullable=True)

    # Payload (anonymised)
    properties = db.Column(db.JSON, default=dict)

    # Timing
    duration_ms = db.Column(db.Integer, nullable=True)

    # Source
    source = db.Column(db.String(20), default='api', nullable=False)  # api, frontend, system

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'event_action': self.event_action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'status_code': self.status_code,
            'properties': self.properties,
            'duration_ms': self.duration_ms,
            'source': self.source,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<AnalyticsEvent {self.event_type}:{self.event_action}>'
