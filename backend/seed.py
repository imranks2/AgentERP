"""Seed data for initial platform setup."""
from app import create_app, db
from app.models.user import User
from app.models.subscription import SubscriptionPlan, PlanFeature


def seed_plans():
    """Create default subscription plans."""
    plans = [
        {
            'name': 'Free',
            'slug': 'free',
            'description': 'Get started with basic features. Perfect for small teams exploring the platform.',
            'price_monthly': 0,
            'price_yearly': 0,
            'max_users': 3,
            'max_storage_gb': 1,
            'sort_order': 0,
            'features': [
                {'key': 'module_inventory', 'name': 'Inventory Management', 'enabled': True, 'limit': 100},
                {'key': 'module_sales', 'name': 'Sales', 'enabled': True, 'limit': 50},
                {'key': 'module_purchasing', 'name': 'Purchasing', 'enabled': False},
                {'key': 'module_accounting', 'name': 'Accounting', 'enabled': False},
                {'key': 'module_hr', 'name': 'Human Resources', 'enabled': False},
                {'key': 'module_crm', 'name': 'CRM', 'enabled': False},
                {'key': 'api_access', 'name': 'API Access', 'enabled': True, 'limit': 1000},
                {'key': 'reports', 'name': 'Reports', 'enabled': True, 'limit': 5},
                {'key': 'ai_assistant', 'name': 'AI Assistant', 'enabled': False},
                {'key': 'custom_fields', 'name': 'Custom Fields', 'enabled': False},
            ],
        },
        {
            'name': 'Standard',
            'slug': 'standard',
            'description': 'Everything you need to run your business. Ideal for growing companies.',
            'price_monthly': 49.99,
            'price_yearly': 499.99,
            'max_users': 25,
            'max_storage_gb': 50,
            'sort_order': 1,
            'features': [
                {'key': 'module_inventory', 'name': 'Inventory Management', 'enabled': True, 'limit': 10000},
                {'key': 'module_sales', 'name': 'Sales', 'enabled': True, 'limit': 5000},
                {'key': 'module_purchasing', 'name': 'Purchasing', 'enabled': True, 'limit': 5000},
                {'key': 'module_accounting', 'name': 'Accounting', 'enabled': True},
                {'key': 'module_hr', 'name': 'Human Resources', 'enabled': True, 'limit': 25},
                {'key': 'module_crm', 'name': 'CRM', 'enabled': True, 'limit': 5000},
                {'key': 'api_access', 'name': 'API Access', 'enabled': True, 'limit': 50000},
                {'key': 'reports', 'name': 'Reports', 'enabled': True, 'limit': 50},
                {'key': 'ai_assistant', 'name': 'AI Assistant', 'enabled': True, 'limit': 100},
                {'key': 'custom_fields', 'name': 'Custom Fields', 'enabled': True, 'limit': 20},
            ],
        },
        {
            'name': 'Premium',
            'slug': 'premium',
            'description': 'Enterprise-grade features with unlimited access. For organisations that need it all.',
            'price_monthly': 149.99,
            'price_yearly': 1499.99,
            'max_users': 999,
            'max_storage_gb': 500,
            'sort_order': 2,
            'features': [
                {'key': 'module_inventory', 'name': 'Inventory Management', 'enabled': True},
                {'key': 'module_sales', 'name': 'Sales', 'enabled': True},
                {'key': 'module_purchasing', 'name': 'Purchasing', 'enabled': True},
                {'key': 'module_accounting', 'name': 'Accounting', 'enabled': True},
                {'key': 'module_hr', 'name': 'Human Resources', 'enabled': True},
                {'key': 'module_crm', 'name': 'CRM', 'enabled': True},
                {'key': 'api_access', 'name': 'API Access', 'enabled': True},
                {'key': 'reports', 'name': 'Reports', 'enabled': True},
                {'key': 'ai_assistant', 'name': 'AI Assistant', 'enabled': True},
                {'key': 'custom_fields', 'name': 'Custom Fields', 'enabled': True},
            ],
        },
    ]

    for plan_data in plans:
        existing = SubscriptionPlan.query.filter_by(slug=plan_data['slug']).first()
        if existing:
            print(f"  Plan '{plan_data['name']}' already exists, skipping.")
            continue

        plan = SubscriptionPlan(
            name=plan_data['name'],
            slug=plan_data['slug'],
            description=plan_data['description'],
            price_monthly=plan_data['price_monthly'],
            price_yearly=plan_data['price_yearly'],
            max_users=plan_data['max_users'],
            max_storage_gb=plan_data['max_storage_gb'],
            sort_order=plan_data['sort_order'],
        )
        db.session.add(plan)
        db.session.flush()

        for f in plan_data['features']:
            feature = PlanFeature(
                plan_id=plan.id,
                feature_key=f['key'],
                feature_name=f['name'],
                enabled=f.get('enabled', True),
                limit_value=f.get('limit'),
            )
            db.session.add(feature)

        print(f"  Created plan: {plan_data['name']}")

    db.session.commit()


def seed_admin(email, password):
    """Create the platform admin user."""
    existing = User.query.filter_by(email=email, is_platform_admin=True).first()
    if existing:
        print(f"  Platform admin '{email}' already exists, skipping.")
        return existing

    admin = User(
        tenant_id=None,
        email=email,
        first_name='Platform',
        last_name='Admin',
        role='platform_admin',
        is_platform_admin=True,
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"  Created platform admin: {email}")
    return admin


def seed_all():
    """Run all seed functions."""
    import os
    print("Seeding database...")

    print("\n1. Creating subscription plans...")
    seed_plans()

    print("\n2. Creating platform admin...")
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@agenterp.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    seed_admin(admin_email, admin_password)

    print("\nSeeding complete!")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_all()
