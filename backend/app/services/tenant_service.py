"""Tenant service - business logic for tenant management."""
import re
from datetime import datetime, timezone, timedelta
from app import db
from app.models.tenant import Tenant
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.user import User


class TenantService:
    """Handles tenant registration, lifecycle management, and queries."""

    TRIAL_DURATION_DAYS = 14

    @staticmethod
    def create_tenant(name, email, admin_first_name, admin_last_name,
                      admin_password, phone=None, address=None):
        """Register a new tenant with a trial subscription and admin user.

        Returns:
            tuple: (tenant, admin_user) on success
        Raises:
            ValueError: If validation fails
        """
        # Generate slug from name
        slug = TenantService._generate_slug(name)

        # Check uniqueness
        if Tenant.query.filter_by(slug=slug).first():
            raise ValueError(f"A tenant with the name '{name}' already exists")

        if Tenant.query.filter(
            Tenant.users.any(User.email == email)
        ).first():
            # Check if email already exists in any tenant
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                raise ValueError(f"Email '{email}' is already registered")

        # Create tenant
        tenant = Tenant(
            name=name,
            slug=slug,
            email=email,
            phone=phone,
            address=address,
            status='trial',
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=TenantService.TRIAL_DURATION_DAYS),
            settings={'timezone': 'UTC', 'language': 'en', 'currency': 'USD'},
        )
        db.session.add(tenant)
        db.session.flush()  # Get tenant ID

        # Assign free plan
        free_plan = SubscriptionPlan.query.filter_by(slug='free').first()
        if free_plan:
            subscription = Subscription(
                tenant_id=tenant.id,
                plan_id=free_plan.id,
                billing_cycle='monthly',
                status='active',
            )
            db.session.add(subscription)

        # Create admin user for the tenant
        admin_user = User(
            tenant_id=tenant.id,
            email=email,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role='admin',
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)

        db.session.commit()
        return tenant, admin_user

    @staticmethod
    def get_tenant(tenant_id):
        """Get a tenant by ID."""
        return Tenant.query.get(tenant_id)

    @staticmethod
    def get_tenant_by_slug(slug):
        """Get a tenant by slug."""
        return Tenant.query.filter_by(slug=slug).first()

    @staticmethod
    def list_tenants(page=1, per_page=20, status=None, search=None):
        """List tenants with pagination and filters."""
        query = Tenant.query

        if status:
            query = query.filter_by(status=status)

        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Tenant.name.ilike(search_term),
                    Tenant.email.ilike(search_term),
                    Tenant.slug.ilike(search_term),
                )
            )

        query = query.order_by(Tenant.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [t.to_dict() for t in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
        }

    @staticmethod
    def update_tenant(tenant_id, **kwargs):
        """Update tenant details."""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            raise ValueError('Tenant not found')

        allowed_fields = ['name', 'email', 'phone', 'address', 'logo_url',
                          'domain', 'settings']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(tenant, key, value)

        # Regenerate slug if name changed
        if 'name' in kwargs:
            new_slug = TenantService._generate_slug(kwargs['name'])
            existing = Tenant.query.filter(
                Tenant.slug == new_slug, Tenant.id != tenant_id
            ).first()
            if existing:
                raise ValueError(f"A tenant with the name '{kwargs['name']}' already exists")
            tenant.slug = new_slug

        db.session.commit()
        return tenant

    @staticmethod
    def change_status(tenant_id, new_status):
        """Change tenant lifecycle status with validation."""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            raise ValueError('Tenant not found')

        tenant.transition_to(new_status)
        db.session.commit()
        return tenant

    @staticmethod
    def delete_tenant(tenant_id):
        """Permanently delete a tenant and all associated data."""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            raise ValueError('Tenant not found')

        db.session.delete(tenant)
        db.session.commit()
        return True

    @staticmethod
    def get_tenant_stats():
        """Get aggregate statistics across all tenants."""
        total = Tenant.query.count()
        by_status = db.session.query(
            Tenant.status, db.func.count(Tenant.id)
        ).group_by(Tenant.status).all()

        status_counts = {status: count for status, count in by_status}

        return {
            'total': total,
            'by_status': status_counts,
            'trial': status_counts.get('trial', 0),
            'active': status_counts.get('active', 0),
            'suspended': status_counts.get('suspended', 0),
            'churned': status_counts.get('churned', 0),
        }

    @staticmethod
    def _generate_slug(name):
        """Generate a URL-friendly slug from a name."""
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
