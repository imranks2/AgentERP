"""Default event handlers — audit logging, analytics, notifications."""
import uuid
import logging
from app import db
from app.models.event import EventLog, Notification
from app.models.user import User
from app.events.bus import event_bus

logger = logging.getLogger(__name__)

# ── Human-readable event descriptions for notifications ─
EVENT_LABELS = {
    'user.invited':        ('New Team Member', 'invited {email} as {role}'),
    'user.updated':        ('User Updated', 'updated user {email}'),
    'user.activated':      ('User Activated', 'activated user account'),
    'user.deactivated':    ('User Deactivated', 'deactivated user account'),
    'user.deleted':        ('User Removed', 'removed a user'),
    'user.profile_updated': ('Profile Updated', 'updated their profile'),
    'auth.login':          ('Login', '{email} logged in'),
    'auth.register':       ('New Registration', '{email} registered'),
    'inventory.product.created':  ('Product Created', 'added product {name}'),
    'inventory.stock.adjusted':   ('Stock Adjusted', 'adjusted stock for {product}'),
    'sales.quotation.created':    ('Quotation Created', 'created quotation {number}'),
    'sales.quotation.converted':  ('Quotation Converted', 'converted quotation to invoice'),
    'sales.invoice.created':      ('Invoice Created', 'created invoice {number}'),
    'sales.invoice.paid':         ('Invoice Paid', 'invoice {number} marked as paid'),
    'sales.payment.recorded':     ('Payment Received', 'recorded payment of {amount}'),
    'purchasing.order.created':   ('PO Created', 'created purchase order {number}'),
    'purchasing.goods.received':  ('Goods Received', 'received goods for PO {number}'),
    'organisation.unit.created':  ('Unit Created', 'created org unit {name}'),
    'organisation.unit.updated':  ('Unit Updated', 'updated org unit {name}'),
    'module.installed':           ('Module Installed', 'installed module {name}'),
    'module.uninstalled':         ('Module Uninstalled', 'uninstalled module {name}'),
}


def _fmt(template, data):
    """Safe format with fallback."""
    try:
        return template.format(**data)
    except (KeyError, IndexError):
        return template


def register_handlers():
    """Register all default event handlers on the global event_bus."""

    @event_bus.on('*')
    def persist_event(event):
        """Store every event in the persistent event log."""
        try:
            # Check if event already persisted (idempotent for replay)
            existing = EventLog.query.get(event.id)
            if existing:
                return
            entry = EventLog(
                id=event.id,
                event_type=event.type,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                data=event.data,
                source=event.source,
                correlation_id=event.correlation_id,
            )
            db.session.add(entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to persist event {event.type}: {e}')

    @event_bus.on('*')
    def create_notifications(event):
        """Create in-app notifications for relevant tenant users."""
        if not event.tenant_id:
            return
        label = EVENT_LABELS.get(event.type)
        if not label:
            return  # Skip events without notification templates

        title, msg_tpl = label
        message = _fmt(msg_tpl, event.data)

        try:
            # Notify all active users in the tenant (except the actor)
            users = User.query.filter(
                User.tenant_id == event.tenant_id,
                User.is_active.is_(True),
                User.id != event.user_id,
            ).all()

            for user in users:
                notif = Notification(
                    tenant_id=event.tenant_id,
                    user_id=user.id,
                    event_type=event.type,
                    title=title,
                    message=message,
                    data=event.data,
                )
                db.session.add(notif)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to create notifications for {event.type}: {e}')
