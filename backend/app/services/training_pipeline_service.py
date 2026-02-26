"""Training Pipeline Service – manages data export, anonymisation, and model versioning.

Provides the continuous learning loop: collect data → anonymise → train → deploy.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app import db
from app.models.ai import AIInteractionLog
from app.models.analytics import AnalyticsEvent
from app.models.ai_advanced import TrainingDataset, ModelVersion


class TrainingPipelineService:
    """Manages the AI training data pipeline and model lifecycle."""

    # ── Training Datasets ─────────────────────────────────────

    @staticmethod
    def export_training_data(date_from: datetime = None, date_to: datetime = None,
                             version: str = None) -> TrainingDataset:
        """Export and anonymise interaction logs into a training dataset."""
        now = datetime.now(timezone.utc)
        date_to = date_to or now

        # Query AI interaction logs
        q = AIInteractionLog.query
        if date_from:
            q = q.filter(AIInteractionLog.created_at >= date_from)
        q = q.filter(AIInteractionLog.created_at <= date_to)

        logs = q.all()
        records = []
        for log in logs:
            records.append(_anonymise_interaction(log))

        # Query analytics events
        aq = AnalyticsEvent.query
        if date_from:
            aq = aq.filter(AnalyticsEvent.created_at >= date_from)
        aq = aq.filter(AnalyticsEvent.created_at <= date_to)
        analytics = aq.all()
        analytics_records = [_anonymise_analytics(e) for e in analytics]

        # Compute version
        if not version:
            count = TrainingDataset.query.count()
            version = f'1.{count}.0'

        dataset = TrainingDataset(
            version=version,
            record_count=len(records) + len(analytics_records),
            source_types=['ai_interaction_log', 'analytics_event'],
            date_range_start=date_from,
            date_range_end=date_to,
            anonymised=True,
            metadata_info={
                'interaction_logs': len(records),
                'analytics_events': len(analytics_records),
                'feedback_distribution': _feedback_distribution(logs),
                'tool_usage': _tool_usage_stats(logs),
            },
            status='ready',
        )
        db.session.add(dataset)
        db.session.commit()
        return dataset

    @staticmethod
    def list_datasets(page: int = 1, per_page: int = 20) -> Tuple[List[TrainingDataset], int]:
        q = TrainingDataset.query.order_by(TrainingDataset.created_at.desc())
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_dataset(dataset_id: str) -> Optional[TrainingDataset]:
        return TrainingDataset.query.get(dataset_id)

    # ── Model Versions ────────────────────────────────────────

    @staticmethod
    def create_model_version(data: dict) -> ModelVersion:
        """Register a new model version (from training job)."""
        mv = ModelVersion(
            version=data['version'],
            model_type=data['model_type'],
            training_dataset_id=data.get('training_dataset_id'),
            metrics=data.get('metrics'),
            parameters=data.get('parameters'),
            status=data.get('status', 'training'),
        )
        db.session.add(mv)
        db.session.commit()
        return mv

    @staticmethod
    def list_model_versions(model_type: str = None,
                            page: int = 1, per_page: int = 20) -> Tuple[List[ModelVersion], int]:
        q = ModelVersion.query
        if model_type:
            q = q.filter_by(model_type=model_type)
        q = q.order_by(ModelVersion.created_at.desc())
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def activate_model(model_id: str) -> Optional[ModelVersion]:
        """Activate a model version, deactivating others of same type."""
        mv = ModelVersion.query.get(model_id)
        if not mv:
            return None
        # Deactivate siblings
        ModelVersion.query.filter(
            ModelVersion.model_type == mv.model_type,
            ModelVersion.id != mv.id,
        ).update({'is_active': False, 'status': 'retired'})
        mv.is_active = True
        mv.status = 'active'
        mv.activated_at = datetime.now(timezone.utc)
        db.session.commit()
        return mv

    @staticmethod
    def get_active_model(model_type: str) -> Optional[ModelVersion]:
        return ModelVersion.query.filter_by(
            model_type=model_type, is_active=True
        ).first()

    @staticmethod
    def simulate_training(dataset_id: str, model_type: str = 'intent_classifier') -> ModelVersion:
        """Simulate a model training job (for demo — would be async in production).

        Computes quality metrics from feedback data in the dataset.
        """
        ds = TrainingDataset.query.get(dataset_id)
        if not ds:
            raise ValueError('Dataset not found')

        # Generate simulated metrics from actual feedback data
        feedback_dist = ds.metadata_info.get('feedback_distribution', {}) if ds.metadata_info else {}
        thumbs_up = feedback_dist.get('thumbs_up', 0)
        thumbs_down = feedback_dist.get('thumbs_down', 0)
        total_feedback = thumbs_up + thumbs_down
        accuracy = thumbs_up / total_feedback if total_feedback > 0 else 0.75

        count = ModelVersion.query.filter_by(model_type=model_type).count()
        version = f'{model_type}_v{count + 1}'

        mv = ModelVersion(
            version=version,
            model_type=model_type,
            training_dataset_id=dataset_id,
            metrics={
                'accuracy': round(accuracy, 4),
                'precision': round(min(accuracy + 0.05, 1.0), 4),
                'recall': round(max(accuracy - 0.03, 0.0), 4),
                'f1_score': round(accuracy, 4),
                'training_samples': ds.record_count,
                'feedback_samples': total_feedback,
            },
            parameters={
                'model_type': model_type,
                'dataset_version': ds.version,
                'epochs': 10,
            },
            status='evaluating',
            trained_at=datetime.now(timezone.utc),
        )
        db.session.add(mv)
        db.session.commit()
        return mv

    @staticmethod
    def get_pipeline_stats() -> dict:
        """Get overall training pipeline statistics."""
        datasets = TrainingDataset.query.count()
        models = ModelVersion.query.count()
        active_models = ModelVersion.query.filter_by(is_active=True).count()
        total_records = db.session.query(
            db.func.sum(TrainingDataset.record_count)
        ).scalar() or 0

        # Feedback stats
        total_interactions = AIInteractionLog.query.count()
        with_feedback = AIInteractionLog.query.filter(
            AIInteractionLog.feedback.isnot(None)
        ).count()
        positive = AIInteractionLog.query.filter_by(feedback='thumbs_up').count()

        return {
            'total_datasets': datasets,
            'total_models': models,
            'active_models': active_models,
            'total_training_records': total_records,
            'total_interactions': total_interactions,
            'interactions_with_feedback': with_feedback,
            'positive_feedback': positive,
            'feedback_rate': round(with_feedback / total_interactions, 2) if total_interactions > 0 else 0,
            'satisfaction_rate': round(positive / with_feedback, 2) if with_feedback > 0 else 0,
        }


# ── Anonymisation helpers ─────────────────────────────────────

def _hash_id(value: str) -> str:
    """One-way hash for PII removal."""
    return hashlib.sha256(value.encode()).hexdigest()[:16] if value else None


def _anonymise_interaction(log: AIInteractionLog) -> dict:
    return {
        'id': _hash_id(log.id),
        'tenant_hash': _hash_id(log.tenant_id),
        'action_type': log.action_type,
        'input_summary': log.input_summary,
        'output_summary': log.output_summary,
        'tools_used': log.tools_used,
        'feedback': log.feedback,
        'latency_ms': log.latency_ms,
        'tokens_in': log.tokens_in,
        'tokens_out': log.tokens_out,
        'model': log.model,
    }


def _anonymise_analytics(event: AnalyticsEvent) -> dict:
    return {
        'id': _hash_id(event.id),
        'tenant_hash': _hash_id(event.tenant_id),
        'event_type': event.event_type,
        'event_category': event.event_category,
        'event_action': event.event_action,
        'resource_type': event.resource_type,
        'endpoint': event.endpoint,
        'method': event.method,
    }


def _feedback_distribution(logs: list) -> dict:
    dist = {'thumbs_up': 0, 'thumbs_down': 0, 'none': 0}
    for log in logs:
        if log.feedback == 'thumbs_up':
            dist['thumbs_up'] += 1
        elif log.feedback == 'thumbs_down':
            dist['thumbs_down'] += 1
        else:
            dist['none'] += 1
    return dist


def _tool_usage_stats(logs: list) -> dict:
    usage = {}
    for log in logs:
        if log.tools_used:
            for tool in log.tools_used:
                usage[tool] = usage.get(tool, 0) + 1
    return usage
