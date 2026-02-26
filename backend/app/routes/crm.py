"""CRM routes – Phase 8.

Endpoints for Leads, Opportunities, Activities, and Pipeline stats.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.utils.decorators import tenant_required
from app.services.crm_service import CRMService

crm_bp = Blueprint('crm', __name__)


def _tid():
    return get_jwt()['tenant_id']


def _uid():
    return get_jwt_identity()


# ── Leads ────────────────────────────────────────────────────

@crm_bp.route('/leads', methods=['GET'])
@jwt_required()
@tenant_required
def list_leads():
    leads, total = CRMService.list_leads(
        _tid(),
        status=request.args.get('status'),
        source=request.args.get('source'),
        assigned_to=request.args.get('assigned_to'),
        search=request.args.get('search'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(leads=[l.to_dict() for l in leads], total=total)


@crm_bp.route('/leads', methods=['POST'])
@jwt_required()
@tenant_required
def create_lead():
    try:
        lead = CRMService.create_lead(_tid(), request.json)
        return jsonify(lead.to_dict()), 201
    except ValueError as e:
        return jsonify(error=str(e)), 400


@crm_bp.route('/leads/<lead_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_lead(lead_id):
    lead = CRMService.get_lead(_tid(), lead_id)
    if not lead:
        return jsonify(error='Lead not found'), 404
    return jsonify(lead.to_dict())


@crm_bp.route('/leads/<lead_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_lead(lead_id):
    lead = CRMService.update_lead(_tid(), lead_id, request.json)
    if not lead:
        return jsonify(error='Lead not found'), 404
    return jsonify(lead.to_dict())


@crm_bp.route('/leads/<lead_id>', methods=['DELETE'])
@jwt_required()
@tenant_required
def delete_lead(lead_id):
    try:
        CRMService.delete_lead(_tid(), lead_id)
        return jsonify(message='Lead deleted'), 200
    except ValueError as e:
        return jsonify(error=str(e)), 400


@crm_bp.route('/leads/<lead_id>/convert', methods=['POST'])
@jwt_required()
@tenant_required
def convert_lead(lead_id):
    customer_id = request.json.get('customer_id')
    if not customer_id:
        return jsonify(error='customer_id is required'), 400
    try:
        lead = CRMService.convert_lead(_tid(), lead_id, customer_id)
        return jsonify(lead.to_dict())
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ── Opportunities ────────────────────────────────────────────

@crm_bp.route('/opportunities', methods=['GET'])
@jwt_required()
@tenant_required
def list_opportunities():
    opps, total = CRMService.list_opportunities(
        _tid(),
        stage=request.args.get('stage'),
        assigned_to=request.args.get('assigned_to'),
        search=request.args.get('search'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(opportunities=[o.to_dict() for o in opps], total=total)


@crm_bp.route('/opportunities', methods=['POST'])
@jwt_required()
@tenant_required
def create_opportunity():
    try:
        opp = CRMService.create_opportunity(_tid(), request.json)
        return jsonify(opp.to_dict()), 201
    except ValueError as e:
        return jsonify(error=str(e)), 400


@crm_bp.route('/opportunities/<opp_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_opportunity(opp_id):
    opp = CRMService.get_opportunity(_tid(), opp_id)
    if not opp:
        return jsonify(error='Opportunity not found'), 404
    return jsonify(opp.to_dict())


@crm_bp.route('/opportunities/<opp_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_opportunity(opp_id):
    opp = CRMService.update_opportunity(_tid(), opp_id, request.json)
    if not opp:
        return jsonify(error='Opportunity not found'), 404
    return jsonify(opp.to_dict())


@crm_bp.route('/opportunities/<opp_id>', methods=['DELETE'])
@jwt_required()
@tenant_required
def delete_opportunity(opp_id):
    try:
        CRMService.delete_opportunity(_tid(), opp_id)
        return jsonify(message='Opportunity deleted'), 200
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ── Activities ───────────────────────────────────────────────

@crm_bp.route('/activities', methods=['GET'])
@jwt_required()
@tenant_required
def list_activities():
    acts, total = CRMService.list_activities(
        _tid(),
        lead_id=request.args.get('lead_id'),
        opportunity_id=request.args.get('opportunity_id'),
        activity_type=request.args.get('activity_type'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(activities=[a.to_dict() for a in acts], total=total)


@crm_bp.route('/activities', methods=['POST'])
@jwt_required()
@tenant_required
def create_activity():
    try:
        act = CRMService.create_activity(_tid(), request.json, user_id=_uid())
        return jsonify(act.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400


# ── Pipeline Stats ───────────────────────────────────────────

@crm_bp.route('/pipeline', methods=['GET'])
@jwt_required()
@tenant_required
def pipeline_stats():
    return jsonify(CRMService.pipeline_stats(_tid()))


@crm_bp.route('/stats', methods=['GET'])
@jwt_required()
@tenant_required
def crm_stats():
    return jsonify(CRMService.get_stats(_tid()))
