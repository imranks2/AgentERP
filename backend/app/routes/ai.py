"""AI API routes — Phase 7.

Provides endpoints for chat conversations, one-shot queries,
tool listing, and feedback collection.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.ai.services.chat_service import ChatService
from app.ai.tools.registry import registry

ai_bp = Blueprint('ai', __name__)


def _ctx():
    """Extract tenant_id, user_id and permissions from JWT."""
    claims = get_jwt()
    return (
        claims.get('tenant_id'),
        get_jwt_identity(),
        claims.get('permissions', []),
    )


# ── Conversations ─────────────────────────────────────────

@ai_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    tenant_id, user_id, _ = _ctx()
    if not tenant_id:
        return jsonify(error='No tenant context'), 400
    data = request.get_json(silent=True) or {}
    convo = ChatService.create_conversation(tenant_id, user_id, title=data.get('title'))
    return jsonify(conversation=convo.to_dict()), 201


@ai_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    tenant_id, user_id, _ = _ctx()
    if not tenant_id:
        return jsonify(error='No tenant context'), 400
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    items, total = ChatService.list_conversations(tenant_id, user_id, page, per_page)
    return jsonify(conversations=[c.to_dict() for c in items], total=total)


@ai_bp.route('/conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    tenant_id, user_id, _ = _ctx()
    if not tenant_id:
        return jsonify(error='No tenant context'), 400
    convo = ChatService.get_conversation(tenant_id, conversation_id)
    if not convo:
        return jsonify(error='Not found'), 404
    return jsonify(conversation=convo.to_dict(include_messages=True))


@ai_bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    tenant_id, user_id, perms = _ctx()
    if not tenant_id:
        return jsonify(error='No tenant context'), 400
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify(error='Message content is required'), 400
    try:
        result = ChatService.send_message(
            tenant_id, user_id, conversation_id, content,
            user_permissions=perms,
        )
        return jsonify(**result)
    except ValueError as e:
        return jsonify(error=str(e)), 404
    except Exception as e:
        return jsonify(error=f'AI processing error: {e}'), 500


@ai_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    tenant_id, user_id, _ = _ctx()
    if not tenant_id:
        return jsonify(error='No tenant context'), 400
    ok = ChatService.delete_conversation(tenant_id, conversation_id)
    if not ok:
        return jsonify(error='Not found'), 404
    return jsonify(message='Conversation archived'), 200


# ── One-shot Query ────────────────────────────────────────

@ai_bp.route('/query', methods=['POST'])
@jwt_required()
def nl_query():
    """Execute a natural language query without conversation context."""
    tenant_id, user_id, perms = _ctx()
    if not tenant_id:
        return jsonify(error='No tenant context'), 400
    data = request.get_json(silent=True) or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify(error='Query is required'), 400
    try:
        result = ChatService.one_shot_query(tenant_id, user_id, query, user_permissions=perms)
        return jsonify(**result)
    except Exception as e:
        return jsonify(error=f'Query processing error: {e}'), 500


# ── Feedback ──────────────────────────────────────────────

@ai_bp.route('/interactions/<interaction_id>/feedback', methods=['POST'])
@jwt_required()
def submit_feedback(interaction_id):
    data = request.get_json(silent=True) or {}
    feedback = data.get('feedback')
    if feedback not in ('thumbs_up', 'thumbs_down'):
        return jsonify(error='feedback must be thumbs_up or thumbs_down'), 400
    log = ChatService.submit_feedback(interaction_id, feedback)
    if not log:
        return jsonify(error='Interaction not found'), 404
    return jsonify(message='Feedback recorded', interaction=log.to_dict())


# ── Tools Listing ─────────────────────────────────────────

@ai_bp.route('/tools', methods=['GET'])
@jwt_required()
def list_tools():
    """List all available AI tools (for transparency)."""
    _, _, perms = _ctx()
    tools = registry.tools_for_permissions(perms)
    return jsonify(tools=[
        {
            'name': t.name,
            'description': t.description,
            'module': t.module,
            'permissions': t.permissions,
            'parameters': t.parameters,
        }
        for t in tools
    ])
