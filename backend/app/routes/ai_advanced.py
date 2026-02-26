"""Phase 9 – Advanced AI & Self-Learning API routes.

Endpoints for AI suggestions, agent actions (autonomous execution),
workflow patterns, automated workflows, and the training pipeline.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.services.suggestion_service import SuggestionService
from app.services.agent_action_service import AgentActionService
from app.services.workflow_pattern_service import WorkflowPatternService
from app.services.training_pipeline_service import TrainingPipelineService

ai_advanced_bp = Blueprint('ai_advanced', __name__)


def _tid():
    return get_jwt()['tenant_id']


def _uid():
    return get_jwt_identity()


# ── AI Suggestions ────────────────────────────────────────

@ai_advanced_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def list_suggestions():
    items, total = SuggestionService.list_suggestions(
        _tid(),
        user_id=request.args.get('user_id'),
        status=request.args.get('status'),
        category=request.args.get('category'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 20)),
    )
    return jsonify({'suggestions': [s.to_dict() for s in items], 'total': total})


@ai_advanced_bp.route('/suggestions/generate', methods=['POST'])
@jwt_required()
def generate_suggestions():
    results = SuggestionService.generate_all_suggestions(_tid())
    return jsonify({
        'generated': len(results),
        'suggestions': [s.to_dict() for s in results],
    })


@ai_advanced_bp.route('/suggestions/<suggestion_id>', methods=['GET'])
@jwt_required()
def get_suggestion(suggestion_id):
    s = SuggestionService.get_suggestion(_tid(), suggestion_id)
    if not s:
        return jsonify({'error': 'Suggestion not found'}), 404
    return jsonify({'suggestion': s.to_dict()})


@ai_advanced_bp.route('/suggestions/<suggestion_id>/accept', methods=['POST'])
@jwt_required()
def accept_suggestion(suggestion_id):
    s = SuggestionService.accept_suggestion(_tid(), suggestion_id)
    if not s:
        return jsonify({'error': 'Cannot accept suggestion'}), 400
    return jsonify({'suggestion': s.to_dict()})


@ai_advanced_bp.route('/suggestions/<suggestion_id>/dismiss', methods=['POST'])
@jwt_required()
def dismiss_suggestion(suggestion_id):
    s = SuggestionService.dismiss_suggestion(_tid(), suggestion_id)
    if not s:
        return jsonify({'error': 'Cannot dismiss suggestion'}), 400
    return jsonify({'suggestion': s.to_dict()})


@ai_advanced_bp.route('/suggestions/stats', methods=['GET'])
@jwt_required()
def suggestion_stats():
    return jsonify(SuggestionService.get_stats(_tid()))


# ── Agent Actions (Autonomous) ────────────────────────────

@ai_advanced_bp.route('/actions', methods=['GET'])
@jwt_required()
def list_actions():
    items, total = AgentActionService.list_actions(
        _tid(),
        status=request.args.get('status'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 20)),
    )
    return jsonify({'actions': [a.to_dict() for a in items], 'total': total})


@ai_advanced_bp.route('/actions', methods=['POST'])
@jwt_required()
def propose_action():
    data = request.get_json(silent=True) or {}
    if not data.get('action_type'):
        return jsonify({'error': 'action_type required'}), 400
    action = AgentActionService.propose_action(_tid(), _uid(), data)
    return jsonify({'action': action.to_dict()}), 201


@ai_advanced_bp.route('/actions/<action_id>', methods=['GET'])
@jwt_required()
def get_action(action_id):
    a = AgentActionService.get_action(_tid(), action_id)
    if not a:
        return jsonify({'error': 'Action not found'}), 404
    return jsonify({'action': a.to_dict()})


@ai_advanced_bp.route('/actions/<action_id>/approve', methods=['POST'])
@jwt_required()
def approve_action(action_id):
    a = AgentActionService.approve_action(_tid(), action_id, _uid())
    if not a:
        return jsonify({'error': 'Cannot approve action'}), 400
    return jsonify({'action': a.to_dict()})


@ai_advanced_bp.route('/actions/<action_id>/reject', methods=['POST'])
@jwt_required()
def reject_action(action_id):
    a = AgentActionService.reject_action(_tid(), action_id, _uid())
    if not a:
        return jsonify({'error': 'Cannot reject action'}), 400
    return jsonify({'action': a.to_dict()})


@ai_advanced_bp.route('/actions/<action_id>/execute', methods=['POST'])
@jwt_required()
def execute_action(action_id):
    a = AgentActionService.execute_action(_tid(), action_id)
    if not a:
        return jsonify({'error': 'Cannot execute action'}), 400
    return jsonify({'action': a.to_dict()})


@ai_advanced_bp.route('/actions/pending', methods=['GET'])
@jwt_required()
def pending_actions():
    count = AgentActionService.pending_count(_tid())
    return jsonify({'pending_count': count})


@ai_advanced_bp.route('/actions/stats', methods=['GET'])
@jwt_required()
def action_stats():
    return jsonify(AgentActionService.get_stats(_tid()))


# ── Workflow Patterns ─────────────────────────────────────

@ai_advanced_bp.route('/patterns', methods=['GET'])
@jwt_required()
def list_patterns():
    items, total = WorkflowPatternService.list_patterns(
        _tid(),
        status=request.args.get('status'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 20)),
    )
    return jsonify({'patterns': [p.to_dict() for p in items], 'total': total})


@ai_advanced_bp.route('/patterns/detect', methods=['POST'])
@jwt_required()
def detect_patterns():
    min_freq = int(request.args.get('min_frequency', 3))
    patterns = WorkflowPatternService.detect_patterns(_tid(), min_frequency=min_freq)
    return jsonify({
        'detected': len(patterns),
        'patterns': [p.to_dict() for p in patterns],
    })


@ai_advanced_bp.route('/patterns/<pattern_id>/dismiss', methods=['POST'])
@jwt_required()
def dismiss_pattern(pattern_id):
    p = WorkflowPatternService.dismiss_pattern(_tid(), pattern_id)
    if not p:
        return jsonify({'error': 'Pattern not found'}), 404
    return jsonify({'pattern': p.to_dict()})


@ai_advanced_bp.route('/patterns/<pattern_id>/activate', methods=['POST'])
@jwt_required()
def activate_pattern(pattern_id):
    wf = WorkflowPatternService.activate_pattern_as_workflow(_tid(), pattern_id, _uid())
    if not wf:
        return jsonify({'error': 'Pattern not found'}), 404
    return jsonify({'workflow': wf.to_dict()}), 201


# ── Automated Workflows ──────────────────────────────────

@ai_advanced_bp.route('/workflows', methods=['GET'])
@jwt_required()
def list_workflows():
    items, total = WorkflowPatternService.list_workflows(
        _tid(),
        active_only=request.args.get('active_only', 'false').lower() == 'true',
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 20)),
    )
    return jsonify({'workflows': [w.to_dict() for w in items], 'total': total})


@ai_advanced_bp.route('/workflows', methods=['POST'])
@jwt_required()
def create_workflow():
    data = request.get_json(silent=True) or {}
    if not data.get('name') or not data.get('steps'):
        return jsonify({'error': 'name and steps required'}), 400
    data['created_by'] = _uid()
    wf = WorkflowPatternService.create_workflow(_tid(), data)
    return jsonify({'workflow': wf.to_dict()}), 201


@ai_advanced_bp.route('/workflows/<workflow_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_workflow(workflow_id):
    wf = WorkflowPatternService.toggle_workflow(_tid(), workflow_id)
    if not wf:
        return jsonify({'error': 'Workflow not found'}), 404
    return jsonify({'workflow': wf.to_dict()})


@ai_advanced_bp.route('/workflows/stats', methods=['GET'])
@jwt_required()
def workflow_stats():
    return jsonify(WorkflowPatternService.get_stats(_tid()))


# ── Training Pipeline ────────────────────────────────────

@ai_advanced_bp.route('/training/export', methods=['POST'])
@jwt_required()
def export_training_data():
    data = request.get_json(silent=True) or {}
    ds = TrainingPipelineService.export_training_data(
        version=data.get('version'),
    )
    return jsonify({'dataset': ds.to_dict()}), 201


@ai_advanced_bp.route('/training/datasets', methods=['GET'])
@jwt_required()
def list_datasets():
    items, total = TrainingPipelineService.list_datasets(
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 20)),
    )
    return jsonify({'datasets': [d.to_dict() for d in items], 'total': total})


@ai_advanced_bp.route('/training/datasets/<dataset_id>', methods=['GET'])
@jwt_required()
def get_dataset(dataset_id):
    ds = TrainingPipelineService.get_dataset(dataset_id)
    if not ds:
        return jsonify({'error': 'Dataset not found'}), 404
    return jsonify({'dataset': ds.to_dict()})


@ai_advanced_bp.route('/training/train', methods=['POST'])
@jwt_required()
def train_model():
    data = request.get_json(silent=True) or {}
    if not data.get('dataset_id'):
        return jsonify({'error': 'dataset_id required'}), 400
    try:
        mv = TrainingPipelineService.simulate_training(
            data['dataset_id'],
            model_type=data.get('model_type', 'intent_classifier'),
        )
        return jsonify({'model': mv.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@ai_advanced_bp.route('/training/models', methods=['GET'])
@jwt_required()
def list_models():
    items, total = TrainingPipelineService.list_model_versions(
        model_type=request.args.get('model_type'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 20)),
    )
    return jsonify({'models': [m.to_dict() for m in items], 'total': total})


@ai_advanced_bp.route('/training/models/<model_id>/activate', methods=['POST'])
@jwt_required()
def activate_model(model_id):
    mv = TrainingPipelineService.activate_model(model_id)
    if not mv:
        return jsonify({'error': 'Model not found'}), 404
    return jsonify({'model': mv.to_dict()})


@ai_advanced_bp.route('/training/stats', methods=['GET'])
@jwt_required()
def training_stats():
    return jsonify(TrainingPipelineService.get_pipeline_stats())
