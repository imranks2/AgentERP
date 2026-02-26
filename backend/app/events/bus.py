"""Core event bus — Redis pub/sub with in-process fallback.

Usage:
    from app.events import event_bus

    # Emit an event
    event_bus.emit('invoice.paid', tenant_id='...', user_id='...', data={...})

    # Subscribe to events
    @event_bus.on('invoice.paid')
    def handle_paid(event):
        ...

    # Subscribe to all events
    @event_bus.on('*')
    def log_all(event):
        ...
"""
import json
import uuid
import threading
import logging
from datetime import datetime, timezone
from collections import defaultdict

logger = logging.getLogger(__name__)


class Event:
    """Immutable event envelope."""

    __slots__ = ('id', 'type', 'tenant_id', 'user_id', 'data',
                 'timestamp', 'correlation_id', 'source')

    def __init__(self, event_type, tenant_id=None, user_id=None, data=None,
                 correlation_id=None, source=None, event_id=None, timestamp=None):
        self.id = event_id or str(uuid.uuid4())
        self.type = event_type
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.data = data or {}
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.correlation_id = correlation_id or self.id
        self.source = source or 'api'

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'data': self.data,
            'timestamp': self.timestamp,
            'correlation_id': self.correlation_id,
            'source': self.source,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, d):
        return cls(
            event_type=d.get('type') or d.get('event_type'),
            tenant_id=d.get('tenant_id'),
            user_id=d.get('user_id'),
            data=d.get('data', {}),
            correlation_id=d.get('correlation_id'),
            source=d.get('source'),
            event_id=d.get('id'),
            timestamp=d.get('timestamp'),
        )

    @classmethod
    def from_json(cls, s):
        return cls.from_dict(json.loads(s))

    def __repr__(self):
        return f'<Event {self.type} id={self.id[:8]}>'


class EventBus:
    """Hybrid event bus: Redis pub/sub when available, in-process fallback."""

    CHANNEL = 'erp:events'

    def __init__(self):
        self._handlers = defaultdict(list)   # event_type -> [handler, ...]
        self._redis = None
        self._pubsub = None
        self._listener_thread = None
        self._app = None

    def init_app(self, app, redis_client=None):
        """Initialise with Flask app and optional Redis client."""
        self._app = app
        self._redis = redis_client
        if self._redis:
            try:
                self._redis.ping()
                self._start_listener()
                logger.info('Event bus: Redis pub/sub mode')
            except Exception:
                self._redis = None
                logger.info('Event bus: in-process mode (Redis unavailable)')
        else:
            logger.info('Event bus: in-process mode')

    def _start_listener(self):
        """Start background thread that listens to Redis channel."""
        if self._listener_thread and self._listener_thread.is_alive():
            return
        self._pubsub = self._redis.pubsub(ignore_subscribe_messages=True)
        self._pubsub.subscribe(self.CHANNEL)

        def _listen():
            try:
                for message in self._pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            event = Event.from_json(message['data'])
                            self._dispatch(event)
                        except Exception as e:
                            logger.error(f'Event dispatch error: {e}')
            except Exception as e:
                logger.error(f'Event listener error: {e}')

        self._listener_thread = threading.Thread(target=_listen, daemon=True, name='event-bus-listener')
        self._listener_thread.start()

    def on(self, event_type):
        """Decorator to register an event handler.

        @event_bus.on('invoice.paid')
        def handle_paid(event):
            ...

        @event_bus.on('*')  # wildcard — all events
        def log_all(event):
            ...
        """
        def decorator(fn):
            self._handlers[event_type].append(fn)
            return fn
        return decorator

    def subscribe(self, event_type, handler):
        """Programmatic subscription."""
        self._handlers[event_type].append(handler)

    def emit(self, event_type, tenant_id=None, user_id=None, data=None,
             correlation_id=None, source=None):
        """Emit an event to all subscribers."""
        event = Event(
            event_type=event_type,
            tenant_id=tenant_id,
            user_id=user_id,
            data=data,
            correlation_id=correlation_id,
            source=source,
        )

        if self._redis:
            try:
                self._redis.publish(self.CHANNEL, event.to_json())
                return event
            except Exception as e:
                logger.warning(f'Redis publish failed, falling back to in-process: {e}')

        # In-process dispatch (no Redis or Redis failed)
        self._dispatch(event)
        return event

    def _dispatch(self, event):
        """Run all matching handlers for an event."""
        handlers = list(self._handlers.get(event.type, []))
        handlers.extend(self._handlers.get('*', []))

        for handler in handlers:
            try:
                if self._app:
                    with self._app.app_context():
                        handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f'Handler {handler.__name__} failed for {event.type}: {e}')

    def replay(self, events):
        """Replay a list of event dicts through handlers."""
        for evt_dict in events:
            event = Event.from_dict(evt_dict) if isinstance(evt_dict, dict) else evt_dict
            self._dispatch(event)


# ── Singleton ───────────────────────────────────────────
event_bus = EventBus()
