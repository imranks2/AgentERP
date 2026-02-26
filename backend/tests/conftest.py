"""Shared test fixtures for AgentERP backend tests."""
import pytest
from app import create_app, db


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register a tenant, return (headers_dict, tenant_data).

    Headers include Bearer token with tenant_id, role='owner', etc.
    """
    resp = client.post('/api/auth/register', json={
        'company_name': 'TestCo',
        'email': 'owner@testco.com',
        'first_name': 'Test',
        'last_name': 'Owner',
        'password': 'Password1!',
    })
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()
    headers = {'Authorization': f"Bearer {data['access_token']}"}
    return headers, data
