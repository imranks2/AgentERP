"""Analytics service - captures user interactions for AI training."""
from datetime import datetime, timezone, timedelta
from app import db
from app.models.analytics import AnalyticsEvent


class AnalyticsService:
    """Manages analytics event capture and querying.

    All events are anonymised and tenant-isolated.
    This data feeds the AI training pipeline in later phases.
    """

    @staticmethod
    def track_event(event_type, event_action, tenant_id=None, user_id=None,
                    session_id=None, event_category='general',
                    resource_type=None, resource_id=None, endpoint=None,
                    method=None, status_code=None, properties=None,
                    duration_ms=None, source='api'):
        """Record an analytics event."""
        event = AnalyticsEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            event_category=event_category,
            event_action=event_action,
            resource_type=resource_type,
            resource_id=resource_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            properties=properties or {},
            duration_ms=duration_ms,
            source=source,
        )
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def track_api_call(request, response, tenant_id=None, user_id=None):
        """Track an API call from request/response objects."""
        return AnalyticsService.track_event(
            event_type='api_call',
            event_action=f'{request.method} {request.path}',
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code if hasattr(response, 'status_code') else None,
            source='api',
        )

    @staticmethod
    def get_events(tenant_id=None, event_type=None, start_date=None,
                   end_date=None, page=1, per_page=50):
        """Query analytics events with filters."""
        query = AnalyticsEvent.query

        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        if event_type:
            query = query.filter_by(event_type=event_type)
        if start_date:
            query = query.filter(AnalyticsEvent.created_at >= start_date)
        if end_date:
            query = query.filter(AnalyticsEvent.created_at <= end_date)

        query = query.order_by(AnalyticsEvent.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [e.to_dict() for e in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
        }

    @staticmethod
    def get_dashboard_stats(tenant_id=None, days=30):
        """Get analytics summary for dashboard display."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        query = AnalyticsEvent.query.filter(AnalyticsEvent.created_at >= cutoff)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        total_events = query.count()

        # Events by type
        by_type = db.session.query(
            AnalyticsEvent.event_type, db.func.count(AnalyticsEvent.id)
        ).filter(AnalyticsEvent.created_at >= cutoff)
        if tenant_id:
            by_type = by_type.filter(AnalyticsEvent.tenant_id == tenant_id)
        by_type = by_type.group_by(AnalyticsEvent.event_type).all()

        # Events per day
        daily = db.session.query(
            db.func.date(AnalyticsEvent.created_at),
            db.func.count(AnalyticsEvent.id)
        ).filter(AnalyticsEvent.created_at >= cutoff)
        if tenant_id:
            daily = daily.filter(AnalyticsEvent.tenant_id == tenant_id)
        daily = daily.group_by(db.func.date(AnalyticsEvent.created_at)).all()

        return {
            'total_events': total_events,
            'by_type': {t: c for t, c in by_type},
            'daily': {str(d): c for d, c in daily},
            'period_days': days,
        }
