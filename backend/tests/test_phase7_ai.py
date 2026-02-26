"""Phase 7 – AI & Agentic Layer tests."""
import json
import pytest
from app import create_app, db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role, Permission
from app.models.ai import Conversation, Message, AIInteractionLog
from app.ai.tools.registry import registry


@pytest.fixture(scope='module')
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='module')
def client(app):
    return app.test_client()


@pytest.fixture(scope='module')
def auth_headers(app, client):
    """Register a tenant + user and return auth headers."""
    with app.app_context():
        res = client.post('/api/auth/register', json={
            'email': 'ai@test.com',
            'password': 'pass123',
            'first_name': 'AI',
            'last_name': 'User',
            'company_name': 'AI Corp',
        })
        assert res.status_code == 201
        token = res.get_json()['access_token']
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='module')
def tenant_id(app, auth_headers, client):
    """Get the tenant_id from the current user."""
    with app.app_context():
        res = client.get('/api/auth/me', headers=auth_headers)
        return res.get_json()['user']['tenant_id']


# ── Tool Registry ──────────────────────────────────────────

class TestToolRegistry:
    def test_tools_registered(self, app):
        """Verify tools were discovered during init."""
        with app.app_context():
            assert len(registry) > 0

    def test_expected_tools_exist(self, app):
        with app.app_context():
            expected = ['list_products', 'list_invoices', 'list_suppliers',
                        'get_org_tree', 'list_users', 'get_sales_stats']
            for name in expected:
                assert registry.get(name) is not None, f'{name} not found in registry'

    def test_tools_filter_by_permissions(self, app):
        with app.app_context():
            # No permissions → might still get some tools with empty permissions
            limited = registry.tools_for_permissions([])
            all_tools = registry.all_tools()
            assert len(limited) <= len(all_tools)

            # With sales.view → should include sales tools
            sales = registry.tools_for_permissions(['sales.view'])
            sales_names = {t.name for t in sales}
            assert 'list_invoices' in sales_names

    def test_openai_function_schema(self, app):
        with app.app_context():
            funcs = registry.to_openai_functions()
            assert len(funcs) > 0
            assert funcs[0]['type'] == 'function'
            assert 'name' in funcs[0]['function']


# ── Mock LLM ──────────────────────────────────────────────

class TestMockLLM:
    def test_mock_decides_invoices(self, app):
        with app.app_context():
            from app.ai.mock_llm import MockLLM
            llm = MockLLM()
            tool_names = {t.name for t in registry.all_tools()}
            decision = llm.decide('show me overdue invoices', tool_names)
            assert decision is not None
            assert decision['name'] == 'list_invoices'
            assert decision['arguments'].get('status') == 'overdue'

    def test_mock_decides_products(self, app):
        with app.app_context():
            from app.ai.mock_llm import MockLLM
            llm = MockLLM()
            tool_names = {t.name for t in registry.all_tools()}
            decision = llm.decide('list all products', tool_names)
            assert decision is not None
            assert decision['name'] == 'list_products'

    def test_mock_fallback(self, app):
        with app.app_context():
            from app.ai.mock_llm import MockLLM
            llm = MockLLM()
            decision = llm.decide('hello there general kenobi', set())
            assert decision is None

    def test_mock_format_response(self, app):
        with app.app_context():
            from app.ai.mock_llm import MockLLM
            llm = MockLLM()
            resp = llm.format_response('hi', None, None)
            assert 'ERP assistant' in resp


# ── Agent ─────────────────────────────────────────────────

class TestERPAgent:
    def test_agent_invoke_mock(self, app, tenant_id):
        with app.app_context():
            from app.ai.agent import ERPAgent
            from app.ai.mock_llm import MockLLM
            agent = ERPAgent(
                llm=MockLLM(),
                tenant_id=tenant_id,
                user_id='test',
                user_permissions=['sales.view', 'inventory.view'],
            )
            result = agent.invoke('show me overdue invoices')
            assert 'content' in result
            assert result['model'] == 'mock'
            assert isinstance(result['tool_calls'], list)

    def test_agent_invoke_unknown_query(self, app, tenant_id):
        with app.app_context():
            from app.ai.agent import ERPAgent
            from app.ai.mock_llm import MockLLM
            agent = ERPAgent(
                llm=MockLLM(),
                tenant_id=tenant_id,
                user_id='test',
                user_permissions=[],
            )
            result = agent.invoke('tell me a joke')
            assert 'content' in result
            assert 'ERP assistant' in result['content']


# ── Chat API ──────────────────────────────────────────────

class TestChatAPI:
    def test_create_conversation(self, client, auth_headers):
        res = client.post('/api/ai/conversations',
                          json={'title': 'Test chat'},
                          headers=auth_headers)
        assert res.status_code == 201
        data = res.get_json()
        assert data['conversation']['title'] == 'Test chat'
        assert data['conversation']['status'] == 'active'

    def test_list_conversations(self, client, auth_headers):
        res = client.get('/api/ai/conversations', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data['total'] >= 1

    def test_send_message(self, client, auth_headers):
        # Create conversation
        res = client.post('/api/ai/conversations',
                          json={'title': 'AI test'},
                          headers=auth_headers)
        convo_id = res.get_json()['conversation']['id']

        # Send message
        res = client.post(f'/api/ai/conversations/{convo_id}/messages',
                          json={'content': 'show me overdue invoices'},
                          headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'assistant_message' in data
        assert data['assistant_message']['role'] == 'assistant'
        assert data['assistant_message']['content']  # non-empty

    def test_get_conversation_with_messages(self, client, auth_headers):
        # Create + send
        res = client.post('/api/ai/conversations', json={}, headers=auth_headers)
        convo_id = res.get_json()['conversation']['id']
        client.post(f'/api/ai/conversations/{convo_id}/messages',
                    json={'content': 'list products'}, headers=auth_headers)

        # Get with messages
        res = client.get(f'/api/ai/conversations/{convo_id}', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert len(data['conversation']['messages']) >= 2  # user + assistant

    def test_delete_conversation(self, client, auth_headers):
        res = client.post('/api/ai/conversations', json={}, headers=auth_headers)
        convo_id = res.get_json()['conversation']['id']
        res = client.delete(f'/api/ai/conversations/{convo_id}', headers=auth_headers)
        assert res.status_code == 200


# ── One-shot Query ────────────────────────────────────────

class TestNLQuery:
    def test_query_endpoint(self, client, auth_headers):
        res = client.post('/api/ai/query',
                          json={'query': 'show me all customers'},
                          headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'answer' in data
        assert 'interaction_id' in data

    def test_query_empty_rejected(self, client, auth_headers):
        res = client.post('/api/ai/query', json={'query': ''}, headers=auth_headers)
        assert res.status_code == 400


# ── Feedback ──────────────────────────────────────────────

class TestFeedback:
    def test_submit_feedback(self, client, auth_headers):
        # Create a query interaction first
        res = client.post('/api/ai/query',
                          json={'query': 'list invoices'},
                          headers=auth_headers)
        interaction_id = res.get_json()['interaction_id']

        # Submit feedback
        res = client.post(f'/api/ai/interactions/{interaction_id}/feedback',
                          json={'feedback': 'thumbs_up'},
                          headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['interaction']['feedback'] == 'thumbs_up'

    def test_invalid_feedback_rejected(self, client, auth_headers):
        res = client.post('/api/ai/interactions/fake-id/feedback',
                          json={'feedback': 'maybe'},
                          headers=auth_headers)
        assert res.status_code == 400


# ── Tools Listing ─────────────────────────────────────────

class TestToolsListing:
    def test_list_tools(self, client, auth_headers):
        res = client.get('/api/ai/tools', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert len(data['tools']) > 0
        tool = data['tools'][0]
        assert 'name' in tool
        assert 'description' in tool
        assert 'module' in tool
