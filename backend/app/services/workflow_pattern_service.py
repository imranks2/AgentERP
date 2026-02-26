"""Workflow Pattern Service – detects and manages automated workflows from user patterns.

Mines analytics events to find repeated action sequences and allows users
to activate them as automated workflows.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app import db
from app.models.analytics import AnalyticsEvent
from app.models.ai_advanced import WorkflowPattern, AutomatedWorkflow


class WorkflowPatternService:
    """Detects patterns and manages automated workflows."""

    # ── Pattern Detection ─────────────────────────────────────

    @staticmethod
    def detect_patterns(tenant_id: str, min_frequency: int = 3) -> List[WorkflowPattern]:
        """Mine analytics events to detect repeated action sequences.

        Looks for common 2-3 step sequences that users repeat frequently.
        """
        events = AnalyticsEvent.query.filter_by(tenant_id=tenant_id) \
            .order_by(AnalyticsEvent.created_at.asc()).all()

        if len(events) < 2:
            return []

        # Build sequences by user session (consecutive events within 10 min)
        sequences = _extract_sequences(events)
        # Count common 2-step and 3-step patterns
        pattern_counts = _count_patterns(sequences)

        new_patterns = []
        for (steps_tuple, count) in pattern_counts.most_common(20):
            if count < min_frequency:
                continue

            steps = [{'action': s[0], 'resource_type': s[1]} for s in steps_tuple]
            name = ' → '.join(s['action'] for s in steps)

            # Skip if pattern already exists for this tenant
            existing = WorkflowPattern.query.filter_by(
                tenant_id=tenant_id, name=name
            ).first()
            if existing:
                existing.frequency = count
                existing.last_seen_at = datetime.now(timezone.utc)
                if existing.confidence < 0.9:
                    existing.confidence = min(0.5 + (count / 20.0), 0.95)
                continue

            pattern = WorkflowPattern(
                tenant_id=tenant_id,
                name=name,
                description=f'Detected pattern: users frequently perform {name} (observed {count} times).',
                steps=steps,
                frequency=count,
                confidence=min(0.5 + (count / 20.0), 0.95),
            )
            db.session.add(pattern)
            new_patterns.append(pattern)

        db.session.commit()
        return new_patterns

    @staticmethod
    def list_patterns(tenant_id: str, status: str = None,
                      page: int = 1, per_page: int = 20) -> Tuple[List[WorkflowPattern], int]:
        q = WorkflowPattern.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        q = q.order_by(WorkflowPattern.frequency.desc())
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_pattern(tenant_id: str, pattern_id: str) -> Optional[WorkflowPattern]:
        return WorkflowPattern.query.filter_by(id=pattern_id, tenant_id=tenant_id).first()

    @staticmethod
    def dismiss_pattern(tenant_id: str, pattern_id: str) -> Optional[WorkflowPattern]:
        p = WorkflowPattern.query.filter_by(id=pattern_id, tenant_id=tenant_id).first()
        if p:
            p.status = 'dismissed'
            db.session.commit()
        return p

    # ── Automated Workflows ───────────────────────────────────

    @staticmethod
    def create_workflow(tenant_id: str, data: dict) -> AutomatedWorkflow:
        wf = AutomatedWorkflow(
            tenant_id=tenant_id,
            pattern_id=data.get('pattern_id'),
            name=data['name'],
            description=data.get('description'),
            trigger_event=data.get('trigger_event'),
            steps=data['steps'],
            is_active=data.get('is_active', False),
            created_by=data.get('created_by'),
        )
        db.session.add(wf)

        # Update pattern status if created from pattern
        if data.get('pattern_id'):
            pattern = WorkflowPattern.query.get(data['pattern_id'])
            if pattern:
                pattern.status = 'activated'

        db.session.commit()
        return wf

    @staticmethod
    def activate_pattern_as_workflow(tenant_id: str, pattern_id: str,
                                    user_id: str) -> Optional[AutomatedWorkflow]:
        """Convert a detected pattern into an active automated workflow."""
        pattern = WorkflowPattern.query.filter_by(
            id=pattern_id, tenant_id=tenant_id
        ).first()
        if not pattern:
            return None

        # Build workflow steps from pattern steps
        wf_steps = []
        for step in pattern.steps:
            wf_steps.append({
                'action': step.get('action'),
                'resource_type': step.get('resource_type'),
                'auto': True,
            })

        wf = AutomatedWorkflow(
            tenant_id=tenant_id,
            pattern_id=pattern_id,
            name=f'Auto: {pattern.name}',
            description=f'Automated workflow generated from detected pattern. '
                        f'Observed {pattern.frequency} times.',
            steps=wf_steps,
            is_active=True,
            created_by=user_id,
        )
        db.session.add(wf)
        pattern.status = 'activated'
        db.session.commit()
        return wf

    @staticmethod
    def list_workflows(tenant_id: str, active_only: bool = False,
                       page: int = 1, per_page: int = 20) -> Tuple[List[AutomatedWorkflow], int]:
        q = AutomatedWorkflow.query.filter_by(tenant_id=tenant_id)
        if active_only:
            q = q.filter_by(is_active=True)
        q = q.order_by(AutomatedWorkflow.created_at.desc())
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_workflow(tenant_id: str, workflow_id: str) -> Optional[AutomatedWorkflow]:
        return AutomatedWorkflow.query.filter_by(id=workflow_id, tenant_id=tenant_id).first()

    @staticmethod
    def toggle_workflow(tenant_id: str, workflow_id: str) -> Optional[AutomatedWorkflow]:
        wf = AutomatedWorkflow.query.filter_by(id=workflow_id, tenant_id=tenant_id).first()
        if wf:
            wf.is_active = not wf.is_active
            db.session.commit()
        return wf

    @staticmethod
    def get_stats(tenant_id: str) -> dict:
        patterns = WorkflowPattern.query.filter_by(tenant_id=tenant_id)
        workflows = AutomatedWorkflow.query.filter_by(tenant_id=tenant_id)

        return {
            'total_patterns': patterns.count(),
            'detected_patterns': patterns.filter_by(status='detected').count(),
            'activated_patterns': patterns.filter_by(status='activated').count(),
            'total_workflows': workflows.count(),
            'active_workflows': workflows.filter_by(is_active=True).count(),
            'total_executions': db.session.query(
                db.func.sum(AutomatedWorkflow.execution_count)
            ).filter(AutomatedWorkflow.tenant_id == tenant_id).scalar() or 0,
        }


# ── Helpers ───────────────────────────────────────────────────

def _extract_sequences(events: list, gap_minutes: int = 10) -> list:
    """Group events into user sessions and extract action sequences."""
    from datetime import timedelta
    sessions = []
    current_session = []

    for i, event in enumerate(events):
        action = (event.event_action or event.event_type, event.resource_type or 'unknown')
        if i == 0:
            current_session.append(action)
            continue

        prev = events[i - 1]
        time_diff = (event.created_at - prev.created_at).total_seconds() / 60
        same_user = event.user_id == prev.user_id

        if same_user and time_diff <= gap_minutes:
            current_session.append(action)
        else:
            if len(current_session) >= 2:
                sessions.append(current_session)
            current_session = [action]

    if len(current_session) >= 2:
        sessions.append(current_session)

    return sessions


def _count_patterns(sessions: list) -> Counter:
    """Count 2-step and 3-step patterns across all sessions."""
    counter = Counter()
    for session in sessions:
        # 2-step patterns
        for i in range(len(session) - 1):
            pair = (session[i], session[i + 1])
            counter[pair] += 1
        # 3-step patterns
        for i in range(len(session) - 2):
            triple = (session[i], session[i + 1], session[i + 2])
            counter[triple] += 1
    return counter
