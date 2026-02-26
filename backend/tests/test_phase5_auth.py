"""Phase 5 – Authentication & Authorization tests.

Covers: RBAC models, user management, permissions, audit logging.
"""
import pytest


class TestRolesAndPermissions:
    """Test role & permission seeding and listing."""

    def test_roles_seeded_on_register(self, auth_headers):
        """Registering a tenant seeds default roles."""
        headers, _ = auth_headers
        from app.models.role import Role
        # Should have system roles for the tenant
        roles = Role.query.filter(Role.is_system.is_(True)).all()
        assert len(roles) >= 5  # owner, admin, manager, user, viewer

    def test_list_roles(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.get('/api/users/roles', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'roles' in data
        slugs = [r['slug'] for r in data['roles']]
        assert 'owner' in slugs
        assert 'admin' in slugs
        assert 'viewer' in slugs

    def test_list_permissions(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.get('/api/users/permissions', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'permissions' in data
        slugs = [p['slug'] for p in data['permissions']]
        assert 'inventory.view' in slugs
        assert 'sales.create' in slugs
        assert 'users.manage' in slugs

    def test_seed_roles_idempotent(self, client, auth_headers):
        """Re-seeding roles does not create duplicates."""
        headers, _ = auth_headers
        resp = client.post('/api/users/seed-roles', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['seeded'] == 0  # Already seeded


class TestUserManagement:
    """Test user invite, list, update, activation, deletion."""

    def test_invite_user(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.post('/api/users/invite', headers=headers, json={
            'email': 'newuser@testco.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'user',
            'password': 'TempPass1!',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['user']['email'] == 'newuser@testco.com'
        assert data['user']['role'] == 'user'

    def test_invite_duplicate_rejected(self, client, auth_headers):
        headers, _ = auth_headers
        payload = {
            'email': 'dup@testco.com',
            'first_name': 'Dup',
            'last_name': 'User',
            'role': 'user',
            'password': 'TempPass1!',
        }
        resp1 = client.post('/api/users/invite', headers=headers, json=payload)
        assert resp1.status_code == 201
        resp2 = client.post('/api/users/invite', headers=headers, json=payload)
        assert resp2.status_code == 400
        assert 'already exists' in resp2.get_json()['error']

    def test_invite_missing_fields(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.post('/api/users/invite', headers=headers, json={
            'email': 'noname@testco.com',
        })
        assert resp.status_code == 400
        assert 'Missing' in resp.get_json()['error']

    def test_list_users(self, client, auth_headers):
        headers, _ = auth_headers
        # Invite a user first
        client.post('/api/users/invite', headers=headers, json={
            'email': 'listed@testco.com', 'first_name': 'Listed', 'last_name': 'User',
            'role': 'user', 'password': 'Pass1!',
        })
        resp = client.get('/api/users/', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 2  # owner + invited user
        emails = [u['email'] for u in data['users']]
        assert 'listed@testco.com' in emails

    def test_get_user(self, client, auth_headers):
        headers, _ = auth_headers
        # Invite
        inv = client.post('/api/users/invite', headers=headers, json={
            'email': 'getme@testco.com', 'first_name': 'Get', 'last_name': 'Me',
            'role': 'viewer', 'password': 'Pass1!',
        })
        user_id = inv.get_json()['user']['id']
        resp = client.get(f'/api/users/{user_id}', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['user']['email'] == 'getme@testco.com'

    def test_update_user_role(self, client, auth_headers):
        headers, _ = auth_headers
        inv = client.post('/api/users/invite', headers=headers, json={
            'email': 'promote@testco.com', 'first_name': 'Pro', 'last_name': 'Mote',
            'role': 'user', 'password': 'Pass1!',
        })
        user_id = inv.get_json()['user']['id']
        resp = client.put(f'/api/users/{user_id}', headers=headers, json={'role': 'manager'})
        assert resp.status_code == 200
        assert resp.get_json()['user']['role'] == 'manager'

    def test_deactivate_user(self, client, auth_headers):
        headers, _ = auth_headers
        inv = client.post('/api/users/invite', headers=headers, json={
            'email': 'disable@testco.com', 'first_name': 'Dis', 'last_name': 'Able',
            'role': 'user', 'password': 'Pass1!',
        })
        user_id = inv.get_json()['user']['id']
        resp = client.put(f'/api/users/{user_id}/activate', headers=headers,
                          json={'is_active': False})
        assert resp.status_code == 200
        assert resp.get_json()['user']['is_active'] is False

    def test_reactivate_user(self, client, auth_headers):
        headers, _ = auth_headers
        inv = client.post('/api/users/invite', headers=headers, json={
            'email': 'reactivate@testco.com', 'first_name': 'Re', 'last_name': 'Act',
            'role': 'user', 'password': 'Pass1!',
        })
        user_id = inv.get_json()['user']['id']
        client.put(f'/api/users/{user_id}/activate', headers=headers, json={'is_active': False})
        resp = client.put(f'/api/users/{user_id}/activate', headers=headers,
                          json={'is_active': True})
        assert resp.status_code == 200
        assert resp.get_json()['user']['is_active'] is True

    def test_delete_user(self, client, auth_headers):
        headers, _ = auth_headers
        inv = client.post('/api/users/invite', headers=headers, json={
            'email': 'todelete@testco.com', 'first_name': 'To', 'last_name': 'Delete',
            'role': 'user', 'password': 'Pass1!',
        })
        user_id = inv.get_json()['user']['id']
        resp = client.delete(f'/api/users/{user_id}', headers=headers)
        assert resp.status_code == 200
        assert 'deleted' in resp.get_json()['message'].lower()

    def test_cannot_delete_last_owner(self, client, auth_headers):
        """The owner who registered cannot be deleted (they're the last owner)."""
        headers, reg_data = auth_headers
        owner_id = reg_data['user']['id']
        resp = client.delete(f'/api/users/{owner_id}', headers=headers)
        assert resp.status_code == 400  # Cannot delete yourself


class TestProfileSelfService:
    """Test self-service profile updates."""

    def test_update_profile_name(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.put('/api/users/profile', headers=headers, json={
            'first_name': 'Updated',
            'last_name': 'Name',
        })
        assert resp.status_code == 200
        assert resp.get_json()['user']['first_name'] == 'Updated'

    def test_change_password(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.put('/api/users/profile', headers=headers, json={
            'current_password': 'Password1!',
            'password': 'NewPassword2!',
        })
        assert resp.status_code == 200

        # Verify new password works
        login_resp = client.post('/api/auth/login', json={
            'email': 'owner@testco.com',
            'password': 'NewPassword2!',
        })
        assert login_resp.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.put('/api/users/profile', headers=headers, json={
            'current_password': 'WrongPassword',
            'password': 'NewPassword2!',
        })
        assert resp.status_code == 400
        assert 'incorrect' in resp.get_json()['error'].lower()


class TestAuditLog:
    """Test audit logging."""

    def test_audit_logs_created_on_invite(self, client, auth_headers):
        headers, _ = auth_headers
        client.post('/api/users/invite', headers=headers, json={
            'email': 'audited@testco.com', 'first_name': 'Aud', 'last_name': 'It',
            'role': 'user', 'password': 'Pass1!',
        })
        resp = client.get('/api/users/audit-logs', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        actions = [l['action'] for l in data['logs']]
        assert 'user.invited' in actions

    def test_audit_log_pagination(self, client, auth_headers):
        headers, _ = auth_headers
        # Create multiple audit entries
        for i in range(5):
            client.post('/api/users/invite', headers=headers, json={
                'email': f'batch{i}@testco.com', 'first_name': f'B{i}', 'last_name': 'User',
                'role': 'user', 'password': 'Pass1!',
            })
        resp = client.get('/api/users/audit-logs?per_page=2&page=1', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['logs']) == 2
        assert data['pages'] >= 3


class TestPermissionGating:
    """Test that non-admin users cannot perform admin actions."""

    def test_viewer_cannot_invite(self, client, auth_headers):
        """A viewer-role user cannot invite new users."""
        headers, _ = auth_headers
        # Invite a viewer
        inv = client.post('/api/users/invite', headers=headers, json={
            'email': 'viewer@testco.com', 'first_name': 'View', 'last_name': 'Er',
            'role': 'viewer', 'password': 'ViewerPass1!',
        })
        assert inv.status_code == 201

        # Login as viewer
        login = client.post('/api/auth/login', json={
            'email': 'viewer@testco.com', 'password': 'ViewerPass1!',
        })
        assert login.status_code == 200
        viewer_headers = {'Authorization': f"Bearer {login.get_json()['access_token']}"}

        # Viewer tries to invite — should fail
        resp = client.post('/api/users/invite', headers=viewer_headers, json={
            'email': 'hacker@testco.com', 'first_name': 'Hack', 'last_name': 'Er',
            'role': 'user', 'password': 'Pass1!',
        })
        assert resp.status_code == 403

    def test_viewer_cannot_see_audit_logs(self, client, auth_headers):
        """A viewer cannot access audit logs."""
        headers, _ = auth_headers
        inv = client.post('/api/users/invite', headers=headers, json={
            'email': 'viewer2@testco.com', 'first_name': 'V2', 'last_name': 'Er',
            'role': 'viewer', 'password': 'ViewerPass1!',
        })
        login = client.post('/api/auth/login', json={
            'email': 'viewer2@testco.com', 'password': 'ViewerPass1!',
        })
        viewer_headers = {'Authorization': f"Bearer {login.get_json()['access_token']}"}
        resp = client.get('/api/users/audit-logs', headers=viewer_headers)
        assert resp.status_code == 403

    def test_cannot_assign_owner_as_non_owner(self, client, auth_headers):
        """An admin cannot assign the owner role."""
        headers, _ = auth_headers
        # Invite an admin
        inv = client.post('/api/users/invite', headers=headers, json={
            'email': 'admin@testco.com', 'first_name': 'Adm', 'last_name': 'In',
            'role': 'admin', 'password': 'AdminPass1!',
        })
        login = client.post('/api/auth/login', json={
            'email': 'admin@testco.com', 'password': 'AdminPass1!',
        })
        admin_headers = {'Authorization': f"Bearer {login.get_json()['access_token']}"}

        # Admin tries to invite an owner — should fail
        resp = client.post('/api/users/invite', headers=admin_headers, json={
            'email': 'newowner@testco.com', 'first_name': 'New', 'last_name': 'Owner',
            'role': 'owner', 'password': 'Pass1!',
        })
        assert resp.status_code == 403
