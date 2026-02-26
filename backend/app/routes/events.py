"""Event & notification routes."""
import json
import time
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.event_service import EventService
from app.events import event_bus
from app.utils.decorators import tenant_required

events_bp = Blueprint('events', __name__)


# ── Event History ──────────────────────────────────────

@events_bp.route('/history', methods=['GET'])
@jwt_required()
@tenant_required
def event_history():
    """Get event history for the current tenant."""
    claims = get_jwt()
    result = EventService.list_events(
        tenant_id=claims['tenant_id'],
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 50, type=int),
        event_type=request.args.get('event_type'),
    )
    return jsonify(result)


@events_bp.route('/replay', methods=['POST'])
@jwt_required()
@tenant_required
def replay_events():
    """Replay events through handlers (admin only)."""
    claims = get_jwt()
    if claims.get('role') not in ('owner', 'admin') and not claims.get('is_platform_admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json() or {}
    events_data = EventService.get_events_for_replay(
        tenant_id=claims['tenant_id'],
        event_type=data.get('event_type'),
        since=data.get('since'),
        limit=data.get('limit', 100),
    )
    event_bus.replay(events_data)
    return jsonify({'message': f'Replayed {len(events_data)} events', 'count': len(events_data)})


# ── SSE Stream ─────────────────────────────────────────

@events_bp.route('/stream', methods=['GET'])
@jwt_required()
@tenant_required
def event_stream():
    """Server-Sent Events stream for real-time notifications.

    The client connects to this endpoint and receives events as they happen.
    Falls back to polling if Redis is unavailable.
    """
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    user_id = get_jwt_identity()

    def generate():
        # Try Redis pub/sub for real-time
        redis_client = event_bus._redis
        if redis_client:
            pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(event_bus.CHANNEL)
            try:
                yield f"data: {json.dumps({'type': 'connected'})}\n\n"
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            evt = json.loads(message['data'])
                            # Only send events for this tenant
                            if evt.get('tenant_id') == tenant_id and evt.get('user_id') != user_id:
                                yield f"data: {json.dumps(evt)}\n\n"
                        except (json.JSONDecodeError, KeyError):
                            pass
            finally:
                pubsub.unsubscribe()
                pubsub.close()
        else:
            # Polling fallback — send unread count every 5s
            yield f"data: {json.dumps({'type': 'connected', 'mode': 'polling'})}\n\n"
            for _ in range(60):  # ~5 min then reconnect
                try:
                    count = EventService.unread_count(user_id, tenant_id)
                    yield f"data: {json.dumps({'type': 'unread_count', 'count': count})}\n\n"
                except Exception:
                    pass
                time.sleep(5)

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )


# ── Notifications ──────────────────────────────────────

@events_bp.route('/notifications', methods=['GET'])
@jwt_required()
@tenant_required
def list_notifications():
    """Get notifications for the current user."""
    claims = get_jwt()
    user_id = get_jwt_identity()
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    result = EventService.list_notifications(
        user_id=user_id,
        tenant_id=claims['tenant_id'],
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 20, type=int),
        unread_only=unread_only,
    )
    return jsonify(result)


@events_bp.route('/notifications/unread-count', methods=['GET'])
@jwt_required()
@tenant_required
def unread_count():
    """Get count of unread notifications."""
    claims = get_jwt()
    count = EventService.unread_count(get_jwt_identity(), claims['tenant_id'])
    return jsonify({'unread_count': count})


@events_bp.route('/notifications/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notification_id):
    """Mark a notification as read."""
    try:
        notif = EventService.mark_read(notification_id, get_jwt_identity())
        return jsonify({'notification': notif.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@events_bp.route('/notifications/read-all', methods=['PUT'])
@jwt_required()
@tenant_required
def mark_all_read():
    """Mark all notifications as read."""
    claims = get_jwt()
    EventService.mark_all_read(get_jwt_identity(), claims['tenant_id'])
    return jsonify({'message': 'All notifications marked as read'})
