"""Analytics routes for event tracking and reporting."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.analytics_service import AnalyticsService
from app.utils.decorators import platform_admin_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/track', methods=['POST'])
@jwt_required()
def track_event():
    """Track a frontend analytics event."""
    claims = get_jwt()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    event = AnalyticsService.track_event(
        event_type=data.get('event_type', 'interaction'),
        event_action=data.get('event_action', 'unknown'),
        tenant_id=claims.get('tenant_id'),
        user_id=get_jwt_identity(),
        event_category=data.get('event_category', 'frontend'),
        resource_type=data.get('resource_type'),
        resource_id=data.get('resource_id'),
        properties=data.get('properties', {}),
        source='frontend',
    )
    return jsonify({'id': event.id}), 201


@analytics_bp.route('/events', methods=['GET'])
@jwt_required()
@platform_admin_required
def list_events():
    """List analytics events (platform admin only)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    tenant_id = request.args.get('tenant_id')
    event_type = request.args.get('event_type')

    result = AnalyticsService.get_events(
        tenant_id=tenant_id,
        event_type=event_type,
        page=page,
        per_page=per_page,
    )
    return jsonify(result)


@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@platform_admin_required
def analytics_dashboard():
    """Get analytics dashboard (platform admin only)."""
    days = request.args.get('days', 30, type=int)
    stats = AnalyticsService.get_dashboard_stats(days=days)
    return jsonify(stats)
