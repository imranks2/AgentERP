"""Subscription service - business logic for plans and subscriptions."""
from datetime import datetime, timezone
from app import db
from app.models.subscription import SubscriptionPlan, Subscription, PlanFeature
from app.models.tenant import Tenant


class SubscriptionService:
    """Manages subscription plans, tenant subscriptions, and feature gating."""

    @staticmethod
    def create_plan(name, slug, description=None, price_monthly=0,
                    price_yearly=0, currency='USD', max_users=1,
                    max_storage_gb=1, sort_order=0, features=None):
        """Create a new subscription plan."""
        if SubscriptionPlan.query.filter_by(slug=slug).first():
            raise ValueError(f"Plan with slug '{slug}' already exists")

        plan = SubscriptionPlan(
            name=name,
            slug=slug,
            description=description,
            price_monthly=price_monthly,
            price_yearly=price_yearly,
            currency=currency,
            max_users=max_users,
            max_storage_gb=max_storage_gb,
            sort_order=sort_order,
        )
        db.session.add(plan)
        db.session.flush()

        # Add features
        if features:
            for f in features:
                feature = PlanFeature(
                    plan_id=plan.id,
                    feature_key=f['key'],
                    feature_name=f['name'],
                    enabled=f.get('enabled', True),
                    limit_value=f.get('limit'),
                )
                db.session.add(feature)

        db.session.commit()
        return plan

    @staticmethod
    def get_plan(plan_id):
        """Get a plan by ID."""
        return SubscriptionPlan.query.get(plan_id)

    @staticmethod
    def get_plan_by_slug(slug):
        """Get a plan by slug."""
        return SubscriptionPlan.query.filter_by(slug=slug).first()

    @staticmethod
    def list_plans(active_only=True):
        """List all subscription plans."""
        query = SubscriptionPlan.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(SubscriptionPlan.sort_order).all()

    @staticmethod
    def update_plan(plan_id, **kwargs):
        """Update a subscription plan."""
        plan = SubscriptionPlan.query.get(plan_id)
        if not plan:
            raise ValueError('Plan not found')

        allowed_fields = ['name', 'description', 'price_monthly', 'price_yearly',
                          'currency', 'max_users', 'max_storage_gb', 'is_active',
                          'sort_order']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(plan, key, value)

        db.session.commit()
        return plan

    @staticmethod
    def subscribe_tenant(tenant_id, plan_slug, billing_cycle='monthly'):
        """Subscribe a tenant to a plan (or change plan)."""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            raise ValueError('Tenant not found')

        plan = SubscriptionPlan.query.filter_by(slug=plan_slug, is_active=True).first()
        if not plan:
            raise ValueError(f"Plan '{plan_slug}' not found or inactive")

        # Check for existing subscription
        subscription = Subscription.query.filter_by(tenant_id=tenant_id).first()
        if subscription:
            # Update existing
            subscription.plan_id = plan.id
            subscription.billing_cycle = billing_cycle
            subscription.status = 'active'
            subscription.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            subscription = Subscription(
                tenant_id=tenant_id,
                plan_id=plan.id,
                billing_cycle=billing_cycle,
                status='active',
            )
            db.session.add(subscription)

        # Activate tenant if in trial
        if tenant.status == 'trial':
            tenant.status = 'active'

        db.session.commit()
        return subscription

    @staticmethod
    def get_tenant_subscription(tenant_id):
        """Get a tenant's current subscription with plan details."""
        return Subscription.query.filter_by(tenant_id=tenant_id).first()

    @staticmethod
    def check_feature(tenant_id, feature_key):
        """Check if a tenant has access to a specific feature.

        Returns:
            dict: {'allowed': bool, 'limit': int|None}
        """
        subscription = Subscription.query.filter_by(
            tenant_id=tenant_id, status='active'
        ).first()
        if not subscription:
            return {'allowed': False, 'limit': None}

        feature = PlanFeature.query.filter_by(
            plan_id=subscription.plan_id,
            feature_key=feature_key,
        ).first()

        if not feature:
            return {'allowed': False, 'limit': None}

        return {
            'allowed': feature.enabled,
            'limit': feature.limit_value,
        }

    @staticmethod
    def cancel_subscription(tenant_id):
        """Cancel a tenant's subscription."""
        subscription = Subscription.query.filter_by(tenant_id=tenant_id).first()
        if not subscription:
            raise ValueError('No subscription found')

        subscription.status = 'cancelled'
        subscription.cancelled_at = datetime.now(timezone.utc)
        db.session.commit()
        return subscription

    @staticmethod
    def get_subscription_stats():
        """Get subscription statistics."""
        total = Subscription.query.count()
        by_plan = db.session.query(
            SubscriptionPlan.name, db.func.count(Subscription.id)
        ).join(SubscriptionPlan).group_by(SubscriptionPlan.name).all()

        by_status = db.session.query(
            Subscription.status, db.func.count(Subscription.id)
        ).group_by(Subscription.status).all()

        return {
            'total': total,
            'by_plan': {name: count for name, count in by_plan},
            'by_status': {status: count for status, count in by_status},
        }
