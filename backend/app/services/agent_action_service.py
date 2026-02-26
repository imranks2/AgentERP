"""Agent Action Service – manages autonomous agent actions with approval workflow.

Handles proposing, approving, rejecting, and executing autonomous agent actions.
Actions are classified by risk level which determines approval requirements.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app import db
from app.models.ai_advanced import AgentAction
from app.ai.tools.registry import registry


# Risk classification: actions below this confidence require approval
RISK_THRESHOLDS = {
    'low': 0.8,       # auto-execute above 80% confidence
    'medium': 1.1,    # always require approval (threshold > 1.0 = never auto)
    'high': 1.1,
    'critical': 1.1,
}


class AgentActionService:
    """Manages autonomous agent actions with risk-based approval."""

    @staticmethod
    def propose_action(tenant_id: str, user_id: str, data: dict) -> AgentAction:
        """Propose a new autonomous action.

        Actions at 'low' risk with high confidence are auto-approved.
        All others require explicit approval.
        """
        risk = data.get('risk_level', 'medium')
        confidence = data.get('confidence', 0.5)
        threshold = RISK_THRESHOLDS.get(risk, 1.1)
        auto_approve = confidence >= threshold and risk == 'low'

        action = AgentAction(
            tenant_id=tenant_id,
            user_id=user_id,
            action_type=data['action_type'],
            description=data.get('description'),
            tool_name=data.get('tool_name'),
            parameters=data.get('parameters'),
            confidence=confidence,
            reasoning=data.get('reasoning'),
            risk_level=risk,
            requires_approval=not auto_approve,
            status='approved' if auto_approve else 'proposed',
            approved_at=datetime.now(timezone.utc) if auto_approve else None,
        )
        db.session.add(action)
        db.session.commit()

        # Auto-execute low-risk actions
        if auto_approve:
            AgentActionService.execute_action(tenant_id, action.id)

        return action

    @staticmethod
    def list_actions(tenant_id: str, status: str = None,
                     page: int = 1, per_page: int = 20) -> Tuple[List[AgentAction], int]:
        q = AgentAction.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        q = q.order_by(AgentAction.created_at.desc())
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_action(tenant_id: str, action_id: str) -> Optional[AgentAction]:
        return AgentAction.query.filter_by(id=action_id, tenant_id=tenant_id).first()

    @staticmethod
    def approve_action(tenant_id: str, action_id: str, approved_by: str) -> Optional[AgentAction]:
        action = AgentAction.query.filter_by(id=action_id, tenant_id=tenant_id).first()
        if not action or action.status != 'proposed':
            return None
        action.status = 'approved'
        action.approved_by = approved_by
        action.approved_at = datetime.now(timezone.utc)
        db.session.commit()
        return action

    @staticmethod
    def reject_action(tenant_id: str, action_id: str, rejected_by: str) -> Optional[AgentAction]:
        action = AgentAction.query.filter_by(id=action_id, tenant_id=tenant_id).first()
        if not action or action.status != 'proposed':
            return None
        action.status = 'rejected'
        action.approved_by = rejected_by  # reuse field for rejector
        action.approved_at = datetime.now(timezone.utc)
        db.session.commit()
        return action

    @staticmethod
    def execute_action(tenant_id: str, action_id: str) -> Optional[AgentAction]:
        """Execute an approved action using the tool registry."""
        action = AgentAction.query.filter_by(id=action_id, tenant_id=tenant_id).first()
        if not action or action.status not in ('approved',):
            return None

        if action.tool_name:
            tool = registry.get(action.tool_name)
            if tool:
                try:
                    result = tool.fn(tenant_id, **(action.parameters or {}))
                    action.result = result
                    action.status = 'executed'
                except Exception as e:
                    action.result = {'error': str(e)}
                    action.status = 'failed'
            else:
                action.result = {'error': f'Tool {action.tool_name} not found'}
                action.status = 'failed'
        else:
            action.status = 'executed'

        action.executed_at = datetime.now(timezone.utc)
        db.session.commit()
        return action

    @staticmethod
    def pending_count(tenant_id: str) -> int:
        return AgentAction.query.filter_by(
            tenant_id=tenant_id, status='proposed'
        ).count()

    @staticmethod
    def get_stats(tenant_id: str) -> dict:
        base = AgentAction.query.filter_by(tenant_id=tenant_id)
        total = base.count()
        proposed = base.filter_by(status='proposed').count()
        approved = base.filter_by(status='approved').count()
        executed = base.filter_by(status='executed').count()
        rejected = base.filter_by(status='rejected').count()
        failed = base.filter_by(status='failed').count()
        auto = base.filter_by(requires_approval=False).count()

        return {
            'total_actions': total,
            'proposed': proposed,
            'approved': approved,
            'executed': executed,
            'rejected': rejected,
            'failed': failed,
            'auto_executed': auto,
        }
