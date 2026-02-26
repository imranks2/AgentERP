"""Phase 9 – Advanced AI & Self-Learning tests."""
import json
import pytest
from app import create_app, db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.ai_advanced import (
    AISuggestion, AgentAction, WorkflowPattern, AutomatedWorkflow,
    TrainingDataset, ModelVersion,
)


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
    with app.app_context():
        res = client.post('/api/auth/register', json={
            'email': 'ai9@test.com',
            'password': 'pass123',
            'first_name': 'AI',
            'last_name': 'Nine',
            'company_name': 'AI9 Corp',
        })
        assert res.status_code == 201
        token = res.get_json()['access_token']
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='module')
def tenant_id(app, auth_headers, client):
    with app.app_context():
        res = client.get('/api/auth/me', headers=auth_headers)
        return res.get_json()['user']['tenant_id']


# ── AI Suggestions ─────────────────────────────────────────

class TestAISuggestions:
    def test_list_suggestions_empty(self, client, auth_headers):
        res = client.get('/api/ai/suggestions', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['total'] == 0

    def test_generate_suggestions(self, client, auth_headers):
        res = client.post('/api/ai/suggestions/generate', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'generated' in data

    def test_create_and_accept_suggestion(self, app, client, auth_headers, tenant_id):
        with app.app_context():
            from app.services.suggestion_service import SuggestionService
            s = SuggestionService.create_suggestion(tenant_id, {
                'suggestion_type': 'action',
                'category': 'inventory',
                'title': 'Test Suggestion',
                'description': 'A test suggestion for validation',
                'confidence': 0.85,
                'reasoning': 'Created for testing purposes',
            })
            sid = s.id

        # Get it
        res = client.get(f'/api/ai/suggestions/{sid}', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['suggestion']['status'] == 'pending'

        # Accept it
        res = client.post(f'/api/ai/suggestions/{sid}/accept', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['suggestion']['status'] == 'accepted'

    def test_create_and_dismiss_suggestion(self, app, client, auth_headers, tenant_id):
        with app.app_context():
            from app.services.suggestion_service import SuggestionService
            s = SuggestionService.create_suggestion(tenant_id, {
                'suggestion_type': 'warning',
                'category': 'sales',
                'title': 'Dismiss this one',
                'confidence': 0.6,
            })
            sid = s.id

        res = client.post(f'/api/ai/suggestions/{sid}/dismiss', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['suggestion']['status'] == 'dismissed'

    def test_suggestion_stats(self, client, auth_headers):
        res = client.get('/api/ai/suggestions/stats', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'total_suggestions' in data
        assert 'acceptance_rate' in data

    def test_filter_by_status(self, client, auth_headers):
        res = client.get('/api/ai/suggestions?status=pending', headers=auth_headers)
        assert res.status_code == 200

    def test_filter_by_category(self, client, auth_headers):
        res = client.get('/api/ai/suggestions?category=inventory', headers=auth_headers)
        assert res.status_code == 200


# ── Agent Actions (Autonomy) ──────────────────────────────

class TestAgentActions:
    def test_propose_action(self, client, auth_headers):
        res = client.post('/api/ai/actions', headers=auth_headers, json={
            'action_type': 'create_record',
            'description': 'Create a purchase order for low stock item',
            'tool_name': 'list_products',
            'parameters': {},
            'confidence': 0.7,
            'risk_level': 'medium',
            'reasoning': 'Stock below reorder point',
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['action']['status'] == 'proposed'
        assert data['action']['requires_approval'] is True

    def test_propose_low_risk_auto_approve(self, client, auth_headers):
        """Low-risk actions with high confidence should be auto-executed."""
        res = client.post('/api/ai/actions', headers=auth_headers, json={
            'action_type': 'notification',
            'description': 'Send notification about upcoming deadline',
            'confidence': 0.95,
            'risk_level': 'low',
        })
        assert res.status_code == 201
        data = res.get_json()
        # Low risk + high confidence => auto-approved and auto-executed
        assert data['action']['requires_approval'] is False
        assert data['action']['status'] in ('executed', 'approved')

    def test_approve_and_reject_actions(self, client, auth_headers):
        # Propose two actions
        res1 = client.post('/api/ai/actions', headers=auth_headers, json={
            'action_type': 'update_record',
            'confidence': 0.5,
            'risk_level': 'high',
        })
        res2 = client.post('/api/ai/actions', headers=auth_headers, json={
            'action_type': 'delete_record',
            'confidence': 0.3,
            'risk_level': 'critical',
        })
        a1_id = res1.get_json()['action']['id']
        a2_id = res2.get_json()['action']['id']

        # Approve first
        res = client.post(f'/api/ai/actions/{a1_id}/approve', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['action']['status'] == 'approved'

        # Reject second
        res = client.post(f'/api/ai/actions/{a2_id}/reject', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['action']['status'] == 'rejected'

    def test_list_actions(self, client, auth_headers):
        res = client.get('/api/ai/actions', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['total'] > 0

    def test_pending_count(self, client, auth_headers):
        res = client.get('/api/ai/actions/pending', headers=auth_headers)
        assert res.status_code == 200
        assert 'pending_count' in res.get_json()

    def test_action_stats(self, client, auth_headers):
        res = client.get('/api/ai/actions/stats', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'total_actions' in data
        assert 'auto_executed' in data

    def test_action_validation(self, client, auth_headers):
        res = client.post('/api/ai/actions', headers=auth_headers, json={})
        assert res.status_code == 400


# ── Workflow Patterns ──────────────────────────────────────

class TestWorkflowPatterns:
    def test_detect_patterns(self, client, auth_headers):
        """Pattern detection should work even with no data."""
        res = client.post('/api/ai/patterns/detect', headers=auth_headers)
        assert res.status_code == 200
        assert 'detected' in res.get_json()

    def test_list_patterns(self, client, auth_headers):
        res = client.get('/api/ai/patterns', headers=auth_headers)
        assert res.status_code == 200
        assert 'patterns' in res.get_json()

    def test_create_and_activate_pattern(self, app, client, auth_headers, tenant_id):
        with app.app_context():
            # Create a pattern manually
            pattern = WorkflowPattern(
                tenant_id=tenant_id,
                name='create_quote → create_invoice',
                description='Users frequently create invoice after quote',
                steps=[
                    {'action': 'create', 'resource_type': 'quotation'},
                    {'action': 'create', 'resource_type': 'invoice'},
                ],
                frequency=5,
                confidence=0.75,
            )
            db.session.add(pattern)
            db.session.commit()
            pid = pattern.id

        # Activate it as a workflow
        res = client.post(f'/api/ai/patterns/{pid}/activate', headers=auth_headers)
        assert res.status_code == 201
        wf = res.get_json()['workflow']
        assert wf['is_active'] is True
        assert wf['pattern_id'] == pid

    def test_dismiss_pattern(self, app, client, auth_headers, tenant_id):
        with app.app_context():
            pattern = WorkflowPattern(
                tenant_id=tenant_id,
                name='dismiss_me',
                steps=[{'action': 'test'}],
                frequency=2,
            )
            db.session.add(pattern)
            db.session.commit()
            pid = pattern.id

        res = client.post(f'/api/ai/patterns/{pid}/dismiss', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['pattern']['status'] == 'dismissed'


# ── Automated Workflows ───────────────────────────────────

class TestAutomatedWorkflows:
    def test_create_workflow(self, client, auth_headers):
        res = client.post('/api/ai/workflows', headers=auth_headers, json={
            'name': 'Auto Invoice',
            'description': 'Auto-create invoice when quote is approved',
            'trigger_event': 'sales.quotation.approved',
            'steps': [
                {'tool_name': 'create_invoice', 'parameters': {}, 'condition': None},
            ],
        })
        assert res.status_code == 201
        wf = res.get_json()['workflow']
        assert wf['name'] == 'Auto Invoice'
        assert wf['is_active'] is False

    def test_toggle_workflow(self, app, client, auth_headers, tenant_id):
        with app.app_context():
            wf = AutomatedWorkflow.query.filter_by(tenant_id=tenant_id).first()
            wf_id = wf.id
            was_active = wf.is_active

        # Toggle once
        res = client.post(f'/api/ai/workflows/{wf_id}/toggle', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['workflow']['is_active'] is (not was_active)

        # Toggle back
        res = client.post(f'/api/ai/workflows/{wf_id}/toggle', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['workflow']['is_active'] is was_active

    def test_list_workflows(self, client, auth_headers):
        res = client.get('/api/ai/workflows', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['total'] > 0

    def test_workflow_validation(self, client, auth_headers):
        res = client.post('/api/ai/workflows', headers=auth_headers, json={})
        assert res.status_code == 400

    def test_workflow_stats(self, client, auth_headers):
        res = client.get('/api/ai/workflows/stats', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'total_workflows' in data
        assert 'active_workflows' in data


# ── Training Pipeline ──────────────────────────────────────

class TestTrainingPipeline:
    def test_export_training_data(self, client, auth_headers):
        res = client.post('/api/ai/training/export', headers=auth_headers, json={})
        assert res.status_code == 201
        ds = res.get_json()['dataset']
        assert ds['status'] == 'ready'
        assert ds['anonymised'] is True

    def test_list_datasets(self, client, auth_headers):
        res = client.get('/api/ai/training/datasets', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['total'] > 0

    def test_get_dataset(self, app, client, auth_headers):
        with app.app_context():
            ds = TrainingDataset.query.first()
            ds_id = ds.id

        res = client.get(f'/api/ai/training/datasets/{ds_id}', headers=auth_headers)
        assert res.status_code == 200

    def test_train_model(self, app, client, auth_headers):
        with app.app_context():
            ds = TrainingDataset.query.first()
            ds_id = ds.id

        res = client.post('/api/ai/training/train', headers=auth_headers, json={
            'dataset_id': ds_id,
            'model_type': 'intent_classifier',
        })
        assert res.status_code == 201
        model = res.get_json()['model']
        assert model['model_type'] == 'intent_classifier'
        assert model['status'] == 'evaluating'
        assert 'accuracy' in model['metrics']

    def test_list_models(self, client, auth_headers):
        res = client.get('/api/ai/training/models', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['total'] > 0

    def test_activate_model(self, app, client, auth_headers):
        with app.app_context():
            mv = ModelVersion.query.first()
            mv_id = mv.id

        res = client.post(f'/api/ai/training/models/{mv_id}/activate', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['model']['is_active'] is True
        assert res.get_json()['model']['status'] == 'active'

    def test_training_stats(self, client, auth_headers):
        res = client.get('/api/ai/training/stats', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'total_datasets' in data
        assert 'total_models' in data
        assert 'active_models' in data

    def test_train_validation(self, client, auth_headers):
        res = client.post('/api/ai/training/train', headers=auth_headers, json={})
        assert res.status_code == 400


# ── Confidence & Explainability ──────────────────────────

class TestConfidenceExplainability:
    def test_chat_includes_confidence(self, client, auth_headers):
        """Chat response should include confidence score and reasoning."""
        # Create a conversation
        res = client.post('/api/ai/conversations', headers=auth_headers, json={
            'title': 'Confidence test',
        })
        assert res.status_code == 201
        conv_id = res.get_json()['conversation']['id']

        # Send a message that should match a tool
        res = client.post(f'/api/ai/conversations/{conv_id}/messages',
                          headers=auth_headers, json={'content': 'show me inventory stats'})
        assert res.status_code == 200
        data = res.get_json()
        assert 'confidence' in data
        assert data['confidence'] > 0
        assert 'reasoning' in data
        assert data['reasoning'] is not None

    def test_oneshot_includes_confidence(self, client, auth_headers):
        """One-shot query should include confidence and reasoning."""
        res = client.post('/api/ai/query', headers=auth_headers, json={
            'query': 'list all products',
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'confidence' in data
        assert 'reasoning' in data

    def test_low_confidence_for_unknown(self, client, auth_headers):
        """Unknown queries should have low confidence."""
        res = client.post('/api/ai/query', headers=auth_headers, json={
            'query': 'what is the meaning of life?',
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data['confidence'] == 0.0
        assert data['reasoning'] is not None
