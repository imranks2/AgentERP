"""Subscription and plan management routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.subscription_service import SubscriptionService
from app.utils.decorators import platform_admin_required

subscription_bp = Blueprint('subscriptions', __name__)


@subscription_bp.route('/plans', methods=['GET'])
def list_plans():
    """List available subscription plans (public endpoint)."""
    plans = SubscriptionService.list_plans(active_only=True)
    return jsonify({
        'plans': [p.to_dict(include_features=True) for p in plans]
    })


@subscription_bp.route('/plans', methods=['POST'])
@jwt_required()
@platform_admin_required
def create_plan():
    """Create a new subscription plan (platform admin only)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    required = ['name', 'slug']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

    try:
        plan = SubscriptionService.create_plan(
            name=data['name'],
            slug=data['slug'],
            description=data.get('description'),
            price_monthly=data.get('price_monthly', 0),
            price_yearly=data.get('price_yearly', 0),
            currency=data.get('currency', 'USD'),
            max_users=data.get('max_users', 1),
            max_storage_gb=data.get('max_storage_gb', 1),
            sort_order=data.get('sort_order', 0),
            features=data.get('features'),
        )
        return jsonify({'plan': plan.to_dict(include_features=True)}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@subscription_bp.route('/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Get plan details."""
    plan = SubscriptionService.get_plan(plan_id)
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404
    return jsonify({'plan': plan.to_dict(include_features=True)})


@subscription_bp.route('/plans/<plan_id>', methods=['PUT'])
@jwt_required()
@platform_admin_required
def update_plan(plan_id):
    """Update a subscription plan (platform admin only)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    try:
        plan = SubscriptionService.update_plan(plan_id, **data)
        return jsonify({'plan': plan.to_dict(include_features=True)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@subscription_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def subscribe():
    """Subscribe current tenant to a plan."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'No tenant context'}), 400

    data = request.get_json()
    if not data or 'plan_slug' not in data:
        return jsonify({'error': 'plan_slug is required'}), 400

    try:
        subscription = SubscriptionService.subscribe_tenant(
            tenant_id=tenant_id,
            plan_slug=data['plan_slug'],
            billing_cycle=data.get('billing_cycle', 'monthly'),
        )
        return jsonify({'subscription': subscription.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@subscription_bp.route('/current', methods=['GET'])
@jwt_required()
def current_subscription():
    """Get current tenant's subscription."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'No tenant context'}), 400

    sub = SubscriptionService.get_tenant_subscription(tenant_id)
    if not sub:
        return jsonify({'error': 'No active subscription'}), 404
    return jsonify({'subscription': sub.to_dict()})


@subscription_bp.route('/check-feature/<feature_key>', methods=['GET'])
@jwt_required()
def check_feature(feature_key):
    """Check if current tenant has access to a feature."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'No tenant context'}), 400

    result = SubscriptionService.check_feature(tenant_id, feature_key)
    return jsonify(result)


@subscription_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancel current tenant's subscription."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'No tenant context'}), 400

    try:
        sub = SubscriptionService.cancel_subscription(tenant_id)
        return jsonify({'subscription': sub.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@subscription_bp.route('/stats', methods=['GET'])
@jwt_required()
@platform_admin_required
def subscription_stats():
    """Get subscription statistics (platform admin only)."""
    stats = SubscriptionService.get_subscription_stats()
    return jsonify(stats)
