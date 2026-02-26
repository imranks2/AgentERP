"""User management service — invite, role assignment, profile updates."""
import uuid
from datetime import datetime, timezone
from app import db
from app.models.user import User
from app.models.role import Role, Permission, AuditLog, SYSTEM_PERMISSIONS, SYSTEM_ROLES


class UserService:
    """Business logic for user management within a tenant."""

    # ── Seed default roles & permissions ────────────────

    @staticmethod
    def seed_permissions():
        """Ensure all system permissions exist."""
        created = 0
        for module, action, slug, desc in SYSTEM_PERMISSIONS:
            if not Permission.query.filter_by(slug=slug).first():
                db.session.add(Permission(module=module, action=action, slug=slug, description=desc))
                created += 1
        db.session.commit()
        return created

    @staticmethod
    def seed_roles(tenant_id=None):
        """Ensure all system default roles exist for a tenant (or globally)."""
        UserService.seed_permissions()
        all_perms = {p.slug: p for p in Permission.query.all()}
        created = 0
        for rdef in SYSTEM_ROLES:
            existing = Role.query.filter_by(tenant_id=tenant_id, slug=rdef['slug']).first()
            if existing:
                continue
            role = Role(
                tenant_id=tenant_id,
                name=rdef['name'],
                slug=rdef['slug'],
                description=rdef['description'],
                level=rdef['level'],
                is_system=True,
            )
            if rdef['permissions'] == '*':
                role.permissions = list(all_perms.values())
            else:
                role.permissions = [all_perms[s] for s in rdef['permissions'] if s in all_perms]
            db.session.add(role)
            created += 1
        db.session.commit()
        return created

    # ── User queries ────────────────────────────────────

    @staticmethod
    def list_users(tenant_id, search=None, role_slug=None, is_active=None, page=1, per_page=20):
        """List users for a tenant with optional filters."""
        q = User.query.filter_by(tenant_id=tenant_id)
        if search:
            pat = f'%{search}%'
            q = q.filter(
                db.or_(
                    User.email.ilike(pat),
                    User.first_name.ilike(pat),
                    User.last_name.ilike(pat),
                )
            )
        if role_slug:
            q = q.filter(User.role == role_slug)
        if is_active is not None:
            q = q.filter(User.is_active == is_active)
        q = q.order_by(User.created_at.desc())
        total = q.count()
        users = q.offset((page - 1) * per_page).limit(per_page).all()
        return {
            'users': [u.to_dict() for u in users],
            'total': total,
            'page': page,
            'pages': max(1, (total + per_page - 1) // per_page),
        }

    @staticmethod
    def get_user(user_id, tenant_id):
        """Get a single user (scoped to tenant)."""
        return User.query.filter_by(id=user_id, tenant_id=tenant_id).first()

    # ── Invite & create ─────────────────────────────────

    @staticmethod
    def invite_user(tenant_id, email, first_name, last_name, role_slug='user',
                    password=None, invited_by=None):
        """Invite / create a new user in a tenant."""
        # Check duplicate
        existing = User.query.filter_by(tenant_id=tenant_id, email=email).first()
        if existing:
            raise ValueError(f'A user with email {email} already exists in this tenant')

        # Resolve role
        role_obj = Role.query.filter(
            db.or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
            Role.slug == role_slug,
        ).first()
        if not role_obj:
            raise ValueError(f"Role '{role_slug}' not found")

        user = User(
            tenant_id=tenant_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role_slug,
            role_id=role_obj.id,
            invited_by=invited_by,
        )
        if password:
            user.set_password(password)
        else:
            # Set a random password — user resets via invite link
            user.set_password(str(uuid.uuid4()))

        db.session.add(user)
        db.session.commit()
        return user

    # ── Update ──────────────────────────────────────────

    @staticmethod
    def update_user(user_id, tenant_id, data, updated_by=None):
        """Update user profile / role."""
        user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
        if not user:
            raise ValueError('User not found')

        for field in ('first_name', 'last_name', 'email', 'avatar_url', 'phone'):
            if field in data:
                setattr(user, field, data[field])

        if 'role' in data:
            new_role_slug = data['role']
            # Cannot demote the last owner
            if user.role == 'owner' and new_role_slug != 'owner':
                owner_count = User.query.filter_by(tenant_id=tenant_id, role='owner', is_active=True).count()
                if owner_count <= 1:
                    raise ValueError('Cannot change role of the last owner')

            role_obj = Role.query.filter(
                db.or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
                Role.slug == new_role_slug,
            ).first()
            if role_obj:
                user.role = new_role_slug
                user.role_id = role_obj.id

        if 'password' in data and data['password']:
            user.set_password(data['password'])

        db.session.commit()
        return user

    # ── Activate / deactivate ───────────────────────────

    @staticmethod
    def set_active(user_id, tenant_id, is_active, changed_by=None):
        """Enable or disable a user account."""
        user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
        if not user:
            raise ValueError('User not found')
        if user.role == 'owner' and not is_active:
            owner_count = User.query.filter_by(tenant_id=tenant_id, role='owner', is_active=True).count()
            if owner_count <= 1:
                raise ValueError('Cannot deactivate the last owner')
        user.is_active = is_active
        db.session.commit()
        return user

    # ── Delete ──────────────────────────────────────────

    @staticmethod
    def delete_user(user_id, tenant_id):
        """Permanently delete a user."""
        user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
        if not user:
            raise ValueError('User not found')
        if user.role == 'owner':
            owner_count = User.query.filter_by(tenant_id=tenant_id, role='owner', is_active=True).count()
            if owner_count <= 1:
                raise ValueError('Cannot delete the last owner')
        db.session.delete(user)
        db.session.commit()

    # ── Roles ───────────────────────────────────────────

    @staticmethod
    def list_roles(tenant_id):
        """List all roles available for a tenant (system + custom)."""
        roles = Role.query.filter(
            db.or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None))
        ).order_by(Role.level.desc()).all()
        return [r.to_dict() for r in roles]

    @staticmethod
    def list_permissions():
        """List all permissions."""
        return [p.to_dict() for p in Permission.query.order_by(Permission.module, Permission.action).all()]

    # ── Profile ─────────────────────────────────────────

    @staticmethod
    def update_profile(user_id, data):
        """Update own profile (no role changes)."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')
        for field in ('first_name', 'last_name', 'avatar_url'):
            if field in data:
                setattr(user, field, data[field])
        if 'password' in data and data['password']:
            if 'current_password' not in data:
                raise ValueError('Current password required')
            if not user.check_password(data['current_password']):
                raise ValueError('Current password is incorrect')
            user.set_password(data['password'])
        db.session.commit()
        return user

    # ── Audit logging helper ────────────────────────────

    @staticmethod
    def log_audit(action, tenant_id=None, user_id=None, resource_type=None,
                  resource_id=None, details=None, ip_address=None, user_agent=None):
        """Write an audit log entry."""
        entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    @staticmethod
    def list_audit_logs(tenant_id, page=1, per_page=50, action=None,
                        user_id=None, resource_type=None):
        """Query audit logs for a tenant."""
        q = AuditLog.query.filter_by(tenant_id=tenant_id)
        if action:
            q = q.filter(AuditLog.action.ilike(f'%{action}%'))
        if user_id:
            q = q.filter(AuditLog.user_id == user_id)
        if resource_type:
            q = q.filter(AuditLog.resource_type == resource_type)
        q = q.order_by(AuditLog.created_at.desc())
        total = q.count()
        logs = q.offset((page - 1) * per_page).limit(per_page).all()
        return {
            'logs': [l.to_dict() for l in logs],
            'total': total,
            'page': page,
            'pages': max(1, (total + per_page - 1) // per_page),
        }
