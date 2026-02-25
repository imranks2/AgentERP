"""SaaS Admin panel routes for platform-wide configuration."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.analytics import AnalyticsEvent
from app.services.tenant_service import TenantService
from app.services.subscription_service import SubscriptionService
from app.services.analytics_service import AnalyticsService
from app.utils.decorators import platform_admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@platform_admin_required
def dashboard():
    """Get platform-wide dashboard data."""
    tenant_stats = TenantService.get_tenant_stats()
    subscription_stats = SubscriptionService.get_subscription_stats()
    analytics_stats = AnalyticsService.get_dashboard_stats(days=30)

    # User counts
    total_users = User.query.filter_by(is_platform_admin=False).count()
    active_users = User.query.filter_by(is_active=True, is_platform_admin=False).count()

    return jsonify({
        'tenants': tenant_stats,
        'subscriptions': subscription_stats,
        'analytics': analytics_stats,
        'users': {
            'total': total_users,
            'active': active_users,
        },
    })


@admin_bp.route('/tenants', methods=['GET'])
@jwt_required()
@platform_admin_required
def list_all_tenants():
    """List all tenants with detailed info."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    search = request.args.get('search')

    result = TenantService.list_tenants(
        page=page, per_page=per_page, status=status, search=search
    )

    # Enrich with subscription data
    for item in result['items']:
        sub = Subscription.query.filter_by(tenant_id=item['id']).first()
        item['subscription'] = sub.to_dict() if sub else None
        item['user_count'] = User.query.filter_by(
            tenant_id=item['id'], is_active=True
        ).count()

    return jsonify(result)


@admin_bp.route('/tenants/<tenant_id>', methods=['GET'])
@jwt_required()
@platform_admin_required
def get_tenant_detail(tenant_id):
    """Get detailed tenant information including users and subscription."""
    tenant = TenantService.get_tenant(tenant_id)
    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404

    tenant_data = tenant.to_dict()

    # Add subscription
    sub = Subscription.query.filter_by(tenant_id=tenant_id).first()
    tenant_data['subscription'] = sub.to_dict() if sub else None

    # Add users
    users = User.query.filter_by(tenant_id=tenant_id).all()
    tenant_data['users'] = [u.to_dict() for u in users]

    # Add recent events
    events = AnalyticsService.get_events(tenant_id=tenant_id, page=1, per_page=10)
    tenant_data['recent_events'] = events['items']

    return jsonify({'tenant': tenant_data})


@admin_bp.route('/tenants/<tenant_id>/subscription', methods=['PUT'])
@jwt_required()
@platform_admin_required
def update_tenant_subscription(tenant_id):
    """Change a tenant's subscription plan."""
    data = request.get_json()
    if not data or 'plan_slug' not in data:
        return jsonify({'error': 'plan_slug is required'}), 400

    try:
        sub = SubscriptionService.subscribe_tenant(
            tenant_id=tenant_id,
            plan_slug=data['plan_slug'],
            billing_cycle=data.get('billing_cycle', 'monthly'),
        )
        return jsonify({'subscription': sub.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/platform-config', methods=['GET'])
@jwt_required()
@platform_admin_required
def get_platform_config():
    """Get platform-wide configuration."""
    return jsonify({
        'config': {
            'trial_duration_days': TenantService.TRIAL_DURATION_DAYS,
            'available_plans': [p.to_dict() for p in SubscriptionService.list_plans(active_only=False)],
            'default_plan': 'free',
        }
    })
