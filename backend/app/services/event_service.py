"""Event & notification service."""
from app import db
from app.models.event import EventLog, Notification


class EventService:
    """Queries for event history and notification management."""

    # ── Event History ───────────────────────────────────

    @staticmethod
    def list_events(tenant_id, page=1, per_page=50, event_type=None):
        """Get paginated event history for a tenant."""
        q = EventLog.query.filter_by(tenant_id=tenant_id)
        if event_type:
            q = q.filter(EventLog.event_type.ilike(f'%{event_type}%'))
        q = q.order_by(EventLog.created_at.desc())
        total = q.count()
        events = q.offset((page - 1) * per_page).limit(per_page).all()
        return {
            'events': [e.to_dict() for e in events],
            'total': total,
            'page': page,
            'pages': max(1, (total + per_page - 1) // per_page),
        }

    @staticmethod
    def get_event(event_id):
        """Get a single event by ID."""
        return EventLog.query.get(event_id)

    @staticmethod
    def get_events_for_replay(tenant_id, event_type=None, since=None, limit=1000):
        """Get events for replay (oldest first)."""
        q = EventLog.query.filter_by(tenant_id=tenant_id)
        if event_type:
            q = q.filter(EventLog.event_type == event_type)
        if since:
            q = q.filter(EventLog.created_at >= since)
        q = q.order_by(EventLog.created_at.asc()).limit(limit)
        return [e.to_dict() for e in q.all()]

    # ── Notifications ───────────────────────────────────

    @staticmethod
    def list_notifications(user_id, tenant_id, page=1, per_page=20, unread_only=False):
        """Get paginated notifications for a user."""
        q = Notification.query.filter_by(user_id=user_id, tenant_id=tenant_id)
        if unread_only:
            q = q.filter_by(is_read=False)
        q = q.order_by(Notification.created_at.desc())
        total = q.count()
        notifs = q.offset((page - 1) * per_page).limit(per_page).all()
        return {
            'notifications': [n.to_dict() for n in notifs],
            'total': total,
            'page': page,
            'pages': max(1, (total + per_page - 1) // per_page),
            'unread_count': Notification.query.filter_by(
                user_id=user_id, tenant_id=tenant_id, is_read=False
            ).count(),
        }

    @staticmethod
    def unread_count(user_id, tenant_id):
        """Get count of unread notifications."""
        return Notification.query.filter_by(
            user_id=user_id, tenant_id=tenant_id, is_read=False
        ).count()

    @staticmethod
    def mark_read(notification_id, user_id):
        """Mark a single notification as read."""
        notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notif:
            raise ValueError('Notification not found')
        notif.is_read = True
        db.session.commit()
        return notif

    @staticmethod
    def mark_all_read(user_id, tenant_id):
        """Mark all notifications as read."""
        Notification.query.filter_by(
            user_id=user_id, tenant_id=tenant_id, is_read=False
        ).update({'is_read': True})
        db.session.commit()
