"""AI Suggestion Service – generates and manages proactive AI suggestions.

Analyses usage patterns, business data anomalies, and user behaviour
to generate contextual suggestions that improve over time.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app import db
from app.models.ai_advanced import AISuggestion


class SuggestionService:
    """Generates and manages AI-driven suggestions."""

    # ── CRUD ──────────────────────────────────────────────────

    @staticmethod
    def list_suggestions(tenant_id: str, user_id: str = None,
                         status: str = None, category: str = None,
                         page: int = 1, per_page: int = 20) -> Tuple[List[AISuggestion], int]:
        q = AISuggestion.query.filter_by(tenant_id=tenant_id)
        if user_id:
            q = q.filter((AISuggestion.user_id == user_id) | (AISuggestion.user_id.is_(None)))
        if status:
            q = q.filter_by(status=status)
        if category:
            q = q.filter_by(category=category)
        q = q.order_by(AISuggestion.created_at.desc())
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_suggestion(tenant_id: str, suggestion_id: str) -> Optional[AISuggestion]:
        return AISuggestion.query.filter_by(id=suggestion_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_suggestion(tenant_id: str, data: dict) -> AISuggestion:
        suggestion = AISuggestion(
            tenant_id=tenant_id,
            user_id=data.get('user_id'),
            suggestion_type=data['suggestion_type'],
            category=data.get('category'),
            title=data['title'],
            description=data.get('description'),
            confidence=data.get('confidence', 0.5),
            reasoning=data.get('reasoning'),
            action_data=data.get('action_data'),
            priority=data.get('priority', 'medium'),
        )
        db.session.add(suggestion)
        db.session.commit()
        return suggestion

    @staticmethod
    def accept_suggestion(tenant_id: str, suggestion_id: str) -> Optional[AISuggestion]:
        s = AISuggestion.query.filter_by(id=suggestion_id, tenant_id=tenant_id).first()
        if not s or s.status != 'pending':
            return None
        s.status = 'accepted'
        s.accepted_at = datetime.now(timezone.utc)
        db.session.commit()
        return s

    @staticmethod
    def dismiss_suggestion(tenant_id: str, suggestion_id: str) -> Optional[AISuggestion]:
        s = AISuggestion.query.filter_by(id=suggestion_id, tenant_id=tenant_id).first()
        if not s or s.status != 'pending':
            return None
        s.status = 'dismissed'
        s.dismissed_at = datetime.now(timezone.utc)
        db.session.commit()
        return s

    # ── Pattern-based suggestion generators ───────────────────

    @staticmethod
    def generate_inventory_suggestions(tenant_id: str) -> List[AISuggestion]:
        """Analyse inventory data and generate reorder / anomaly suggestions."""
        from app.models.inventory import Product, StockEntry
        suggestions = []

        # Low-stock detection
        products = Product.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        for product in products:
            stock = StockEntry.query.filter_by(
                tenant_id=tenant_id, product_id=product.id
            ).first()
            if stock and stock.quantity <= product.reorder_point:
                s = SuggestionService.create_suggestion(tenant_id, {
                    'suggestion_type': 'action',
                    'category': 'inventory',
                    'title': f'Reorder {product.name}',
                    'description': f'Stock is at {stock.quantity} units, below reorder point of {product.reorder_point}.',
                    'confidence': 0.9,
                    'reasoning': f'Current stock ({stock.quantity}) ≤ reorder point ({product.reorder_point}). '
                                 f'Based on historical data, a purchase order should be created.',
                    'action_data': {
                        'tool_name': 'create_purchase_order',
                        'arguments': {'product_id': product.id, 'product_name': product.name},
                    },
                    'priority': 'high' if stock.quantity == 0 else 'medium',
                })
                suggestions.append(s)

        return suggestions

    @staticmethod
    def generate_sales_suggestions(tenant_id: str) -> List[AISuggestion]:
        """Analyse sales patterns for insights."""
        from app.models.sales import Invoice
        suggestions = []

        # Overdue invoices
        now = datetime.now(timezone.utc)
        overdue = Invoice.query.filter(
            Invoice.tenant_id == tenant_id,
            Invoice.status == 'sent',
            Invoice.due_date < now,
        ).count()

        if overdue > 0:
            s = SuggestionService.create_suggestion(tenant_id, {
                'suggestion_type': 'warning',
                'category': 'sales',
                'title': f'{overdue} overdue invoice(s) need attention',
                'description': f'There are {overdue} invoices past their due date that haven\'t been paid.',
                'confidence': 1.0,
                'reasoning': 'Overdue invoices detected based on due_date < current date and status = sent.',
                'priority': 'high' if overdue > 5 else 'medium',
            })
            suggestions.append(s)

        return suggestions

    @staticmethod
    def generate_hr_suggestions(tenant_id: str) -> List[AISuggestion]:
        """Analyse HR data for insights."""
        from app.models.hr import LeaveRequest
        suggestions = []

        pending = LeaveRequest.query.filter_by(
            tenant_id=tenant_id, status='pending'
        ).count()

        if pending > 0:
            s = SuggestionService.create_suggestion(tenant_id, {
                'suggestion_type': 'insight',
                'category': 'hr',
                'title': f'{pending} leave request(s) awaiting approval',
                'description': 'Review and approve or reject pending leave requests.',
                'confidence': 1.0,
                'reasoning': 'Pending leave requests detected that need manager action.',
                'priority': 'medium',
            })
            suggestions.append(s)

        return suggestions

    @staticmethod
    def generate_all_suggestions(tenant_id: str) -> List[AISuggestion]:
        """Run all suggestion generators for a tenant."""
        results = []
        generators = [
            SuggestionService.generate_inventory_suggestions,
            SuggestionService.generate_sales_suggestions,
            SuggestionService.generate_hr_suggestions,
        ]
        for gen in generators:
            try:
                results.extend(gen(tenant_id))
            except Exception:
                pass  # individual generator failures shouldn't block others
        return results

    @staticmethod
    def get_stats(tenant_id: str) -> dict:
        base = AISuggestion.query.filter_by(tenant_id=tenant_id)
        total = base.count()
        pending = base.filter_by(status='pending').count()
        accepted = base.filter_by(status='accepted').count()
        dismissed = base.filter_by(status='dismissed').count()
        acceptance_rate = (accepted / (accepted + dismissed)) if (accepted + dismissed) > 0 else 0

        return {
            'total_suggestions': total,
            'pending': pending,
            'accepted': accepted,
            'dismissed': dismissed,
            'acceptance_rate': round(acceptance_rate, 2),
        }
