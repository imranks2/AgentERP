"""Phase 6 – Event-Driven Architecture tests.

Covers: Event bus, event persistence, notifications, SSE stream, replay.
"""
import pytest


class TestEventBus:
    """Test the event bus emit/subscribe/dispatch cycle."""

    def test_event_persisted_on_emit(self, client, auth_headers):
        """Events emitted during user invite are persisted to event_logs."""
        headers, _ = auth_headers
        # Invite a user (triggers user.invited event)
        client.post('/api/users/invite', headers=headers, json={
            'email': 'evt_test@testco.com', 'first_name': 'Evt', 'last_name': 'Test',
            'role': 'user', 'password': 'Pass1!',
        })
        # Check event history
        resp = client.get('/api/events/history', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        types = [e['event_type'] for e in data['events']]
        assert 'user.invited' in types

    def test_auth_events_persisted(self, client, auth_headers):
        """Login and register events are persisted."""
        headers, _ = auth_headers
        resp = client.get('/api/events/history', headers=headers)
        data = resp.get_json()
        types = [e['event_type'] for e in data['events']]
        # Registration emits auth.register
        assert 'auth.register' in types

    def test_event_history_pagination(self, client, auth_headers):
        """Event history supports pagination."""
        headers, _ = auth_headers
        # Create several events
        for i in range(5):
            client.post('/api/users/invite', headers=headers, json={
                'email': f'page_{i}@testco.com', 'first_name': f'P{i}', 'last_name': 'Test',
                'role': 'user', 'password': 'Pass1!',
            })
        resp = client.get('/api/events/history?per_page=2&page=1', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['events']) == 2
        assert data['pages'] >= 3

    def test_event_history_filter_by_type(self, client, auth_headers):
        """Can filter event history by event_type."""
        headers, _ = auth_headers
        client.post('/api/users/invite', headers=headers, json={
            'email': 'filter@testco.com', 'first_name': 'Fil', 'last_name': 'Ter',
            'role': 'user', 'password': 'Pass1!',
        })
        resp = client.get('/api/events/history?event_type=user.invited', headers=headers)
        assert resp.status_code == 200
        for e in resp.get_json()['events']:
            assert 'user.invited' in e['event_type']


class TestNotifications:
    """Test notification creation and management."""

    def test_notifications_created_for_other_users(self, client, auth_headers):
        """When owner invites a user, other users in the tenant get notified."""
        headers, _ = auth_headers
        # First invite user A
        inv_a = client.post('/api/users/invite', headers=headers, json={
            'email': 'notif_a@testco.com', 'first_name': 'A', 'last_name': 'User',
            'role': 'user', 'password': 'Pass1!',
        })
        # Login as A
        login_a = client.post('/api/auth/login', json={
            'email': 'notif_a@testco.com', 'password': 'Pass1!',
        })
        a_headers = {'Authorization': f"Bearer {login_a.get_json()['access_token']}"}

        # Owner invites user B (should notify A)
        client.post('/api/users/invite', headers=headers, json={
            'email': 'notif_b@testco.com', 'first_name': 'B', 'last_name': 'User',
            'role': 'user', 'password': 'Pass1!',
        })

        # A checks notifications
        resp = client.get('/api/events/notifications', headers=a_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['unread_count'] >= 1
        assert any(n['event_type'] == 'user.invited' for n in data['notifications'])

    def test_unread_count(self, client, auth_headers):
        """Unread count endpoint works."""
        headers, _ = auth_headers
        resp = client.get('/api/events/notifications/unread-count', headers=headers)
        assert resp.status_code == 200
        assert 'unread_count' in resp.get_json()

    def test_mark_notification_read(self, client, auth_headers):
        """Can mark a notification as read."""
        headers, _ = auth_headers
        # Invite user to generate notification for owner... owner doesn't get notified by their own action
        # So create a second user first, then login as them
        client.post('/api/users/invite', headers=headers, json={
            'email': 'mark_read@testco.com', 'first_name': 'Mark', 'last_name': 'Read',
            'role': 'admin', 'password': 'Pass1!',
        })
        login = client.post('/api/auth/login', json={
            'email': 'mark_read@testco.com', 'password': 'Pass1!',
        })
        reader_headers = {'Authorization': f"Bearer {login.get_json()['access_token']}"}

        # Owner does something to trigger notification
        client.post('/api/users/invite', headers=headers, json={
            'email': 'trigger@testco.com', 'first_name': 'Trigger', 'last_name': 'Event',
            'role': 'user', 'password': 'Pass1!',
        })

        # Reader gets notifications
        resp = client.get('/api/events/notifications', headers=reader_headers)
        notifs = resp.get_json()['notifications']
        if len(notifs) > 0:
            notif_id = notifs[0]['id']
            mark_resp = client.put(f'/api/events/notifications/{notif_id}/read', headers=reader_headers)
            assert mark_resp.status_code == 200
            assert mark_resp.get_json()['notification']['is_read'] is True

    def test_mark_all_read(self, client, auth_headers):
        """Can mark all notifications as read."""
        headers, _ = auth_headers
        # Invite user, login, trigger events
        client.post('/api/users/invite', headers=headers, json={
            'email': 'allread@testco.com', 'first_name': 'All', 'last_name': 'Read',
            'role': 'admin', 'password': 'Pass1!',
        })
        login = client.post('/api/auth/login', json={
            'email': 'allread@testco.com', 'password': 'Pass1!',
        })
        r_headers = {'Authorization': f"Bearer {login.get_json()['access_token']}"}

        # Trigger some events
        for i in range(3):
            client.post('/api/users/invite', headers=headers, json={
                'email': f'allread_trig{i}@testco.com', 'first_name': f'T{i}', 'last_name': 'User',
                'role': 'user', 'password': 'Pass1!',
            })

        resp = client.put('/api/events/notifications/read-all', headers=r_headers)
        assert resp.status_code == 200

        # Check unread count is 0
        count_resp = client.get('/api/events/notifications/unread-count', headers=r_headers)
        assert count_resp.get_json()['unread_count'] == 0


class TestEventReplay:
    """Test event replay capability."""

    def test_replay_events(self, client, auth_headers):
        """Admin can replay events."""
        headers, _ = auth_headers
        # Generate some events
        client.post('/api/users/invite', headers=headers, json={
            'email': 'replay@testco.com', 'first_name': 'Re', 'last_name': 'Play',
            'role': 'user', 'password': 'Pass1!',
        })

        resp = client.post('/api/events/replay', headers=headers, json={
            'event_type': 'user.invited',
            'limit': 10,
        })
        assert resp.status_code == 200
        assert resp.get_json()['count'] >= 1

    def test_viewer_cannot_replay(self, client, auth_headers):
        """Viewer cannot replay events."""
        headers, _ = auth_headers
        # Create viewer
        client.post('/api/users/invite', headers=headers, json={
            'email': 'replay_viewer@testco.com', 'first_name': 'V', 'last_name': 'R',
            'role': 'viewer', 'password': 'Pass1!',
        })
        login = client.post('/api/auth/login', json={
            'email': 'replay_viewer@testco.com', 'password': 'Pass1!',
        })
        v_headers = {'Authorization': f"Bearer {login.get_json()['access_token']}"}
        resp = client.post('/api/events/replay', headers=v_headers, json={})
        assert resp.status_code == 403


class TestSSEStream:
    """Test SSE stream endpoint availability."""

    def test_stream_requires_auth(self, client):
        """SSE stream requires authentication."""
        resp = client.get('/api/events/stream')
        assert resp.status_code == 401
