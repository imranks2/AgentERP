"""Event-driven architecture — event bus, handlers, and utilities."""
from app.events.bus import EventBus, event_bus

__all__ = ['EventBus', 'event_bus']
