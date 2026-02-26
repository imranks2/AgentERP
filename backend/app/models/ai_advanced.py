"""Phase 9 – Advanced AI & Self-Learning models."""
import uuid
from datetime import datetime, timezone
from app import db


def _uuid():
    return str(uuid.uuid4())


class AISuggestion(db.Model):
    """Proactive AI suggestions generated from user patterns and data analysis."""
    __tablename__ = 'ai_suggestions'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    suggestion_type = db.Column(db.String(30), nullable=False)  # action | insight | warning | automation
    category = db.Column(db.String(50), nullable=True)  # inventory | sales | hr | accounting | crm
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.Float, default=0.5)  # 0.0 – 1.0
    reasoning = db.Column(db.Text, nullable=True)   # explainability — why was this suggested?
    action_data = db.Column(db.JSON, nullable=True)  # {tool_name, arguments} for executable suggestions
    status = db.Column(db.String(20), default='pending')  # pending | accepted | dismissed | executed | expired
    priority = db.Column(db.String(10), default='medium')  # low | medium | high | critical
    expires_at = db.Column(db.DateTime, nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'suggestion_type': self.suggestion_type,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'action_data': self.action_data,
            'status': self.status,
            'priority': self.priority,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AgentAction(db.Model):
    """Tracks autonomous actions proposed or executed by agents."""
    __tablename__ = 'agent_actions'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)  # create_record | update_record | workflow | notification
    description = db.Column(db.Text, nullable=True)
    tool_name = db.Column(db.String(100), nullable=True)
    parameters = db.Column(db.JSON, nullable=True)
    result = db.Column(db.JSON, nullable=True)
    confidence = db.Column(db.Float, default=0.5)
    reasoning = db.Column(db.Text, nullable=True)
    risk_level = db.Column(db.String(10), default='medium')  # low | medium | high | critical
    requires_approval = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='proposed')  # proposed | approved | rejected | executed | failed
    approved_by = db.Column(db.String(36), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'description': self.description,
            'tool_name': self.tool_name,
            'parameters': self.parameters,
            'result': self.result,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'risk_level': self.risk_level,
            'requires_approval': self.requires_approval,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WorkflowPattern(db.Model):
    """Detected patterns from user behaviour for automated workflow suggestions."""
    __tablename__ = 'workflow_patterns'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    steps = db.Column(db.JSON, nullable=False)  # [{action, resource_type, ...}, ...]
    frequency = db.Column(db.Integer, default=1)  # how many times observed
    confidence = db.Column(db.Float, default=0.5)
    status = db.Column(db.String(20), default='detected')  # detected | suggested | activated | dismissed
    last_seen_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    workflows = db.relationship('AutomatedWorkflow', backref='pattern', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'steps': self.steps,
            'frequency': self.frequency,
            'confidence': self.confidence,
            'status': self.status,
            'last_seen_at': self.last_seen_at.isoformat() if self.last_seen_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AutomatedWorkflow(db.Model):
    """User-activated automated workflows derived from detected patterns."""
    __tablename__ = 'automated_workflows'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    pattern_id = db.Column(db.String(36), db.ForeignKey('workflow_patterns.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    trigger_event = db.Column(db.String(100), nullable=True)  # e.g. 'sales.invoice.created'
    steps = db.Column(db.JSON, nullable=False)  # [{tool_name, parameters, condition}, ...]
    is_active = db.Column(db.Boolean, default=False)
    execution_count = db.Column(db.Integer, default=0)
    last_executed_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'pattern_id': self.pattern_id,
            'name': self.name,
            'description': self.description,
            'trigger_event': self.trigger_event,
            'steps': self.steps,
            'is_active': self.is_active,
            'execution_count': self.execution_count,
            'last_executed_at': self.last_executed_at.isoformat() if self.last_executed_at else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TrainingDataset(db.Model):
    """Tracks exported anonymised datasets for model training."""
    __tablename__ = 'training_datasets'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    version = db.Column(db.String(20), nullable=False)  # e.g. '1.0.0'
    record_count = db.Column(db.Integer, default=0)
    source_types = db.Column(db.JSON, nullable=True)  # ['ai_interaction_log', 'analytics_event']
    date_range_start = db.Column(db.DateTime, nullable=True)
    date_range_end = db.Column(db.DateTime, nullable=True)
    anonymised = db.Column(db.Boolean, default=True)
    metadata_info = db.Column(db.JSON, nullable=True)  # stats, coverage metrics
    status = db.Column(db.String(20), default='created')  # created | processing | ready | archived
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'record_count': self.record_count,
            'source_types': self.source_types,
            'date_range_start': self.date_range_start.isoformat() if self.date_range_start else None,
            'date_range_end': self.date_range_end.isoformat() if self.date_range_end else None,
            'anonymised': self.anonymised,
            'metadata_info': self.metadata_info,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ModelVersion(db.Model):
    """Tracks trained model versions and their performance metrics."""
    __tablename__ = 'model_versions'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    version = db.Column(db.String(20), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # intent_classifier | recommendation | anomaly_detector
    training_dataset_id = db.Column(db.String(36), db.ForeignKey('training_datasets.id'), nullable=True)
    metrics = db.Column(db.JSON, nullable=True)  # {accuracy, precision, recall, f1, etc.}
    parameters = db.Column(db.JSON, nullable=True)  # hyperparameters
    status = db.Column(db.String(20), default='training')  # training | evaluating | active | retired
    is_active = db.Column(db.Boolean, default=False)
    trained_at = db.Column(db.DateTime, nullable=True)
    activated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'model_type': self.model_type,
            'training_dataset_id': self.training_dataset_id,
            'metrics': self.metrics,
            'parameters': self.parameters,
            'status': self.status,
            'is_active': self.is_active,
            'trained_at': self.trained_at.isoformat() if self.trained_at else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
