"""CRM service – Leads, Opportunities, Activities, Pipeline stats."""
from datetime import datetime, timezone
from sqlalchemy import func
from app import db
from app.models.crm import Lead, Opportunity, CRMActivity


class CRMService:

    # ── Leads ────────────────────────────────────────────────

    @staticmethod
    def list_leads(tenant_id, status=None, source=None, assigned_to=None,
                   search=None, page=1, per_page=50):
        q = Lead.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        if source:
            q = q.filter_by(source=source)
        if assigned_to:
            q = q.filter_by(assigned_to=assigned_to)
        if search:
            like = f'%{search}%'
            q = q.filter(db.or_(
                Lead.name.ilike(like),
                Lead.email.ilike(like),
                Lead.company.ilike(like),
            ))
        total = q.count()
        leads = q.order_by(Lead.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return leads, total

    @staticmethod
    def get_lead(tenant_id, lead_id):
        return Lead.query.filter_by(id=lead_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_lead(tenant_id, data):
        name = data.get('name', '').strip()
        if not name:
            raise ValueError('Name is required')
        lead = Lead(
            tenant_id=tenant_id, name=name,
            email=data.get('email'), phone=data.get('phone'),
            company=data.get('company'), source=data.get('source', 'web'),
            status=data.get('status', 'new'),
            assigned_to=data.get('assigned_to'),
            score=data.get('score', 0), notes=data.get('notes'),
        )
        db.session.add(lead)
        db.session.commit()
        return lead

    @staticmethod
    def update_lead(tenant_id, lead_id, data):
        lead = Lead.query.filter_by(id=lead_id, tenant_id=tenant_id).first()
        if not lead:
            return None
        for f in ['name', 'email', 'phone', 'company', 'source', 'status',
                   'assigned_to', 'score', 'notes']:
            if f in data:
                setattr(lead, f, data[f])
        lead.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return lead

    @staticmethod
    def delete_lead(tenant_id, lead_id):
        lead = Lead.query.filter_by(id=lead_id, tenant_id=tenant_id).first()
        if not lead:
            raise ValueError('Lead not found')
        db.session.delete(lead)
        db.session.commit()

    @staticmethod
    def convert_lead(tenant_id, lead_id, customer_id):
        """Mark lead as converted and link to customer."""
        lead = Lead.query.filter_by(id=lead_id, tenant_id=tenant_id).first()
        if not lead:
            raise ValueError('Lead not found')
        lead.status = 'converted'
        lead.converted_customer_id = customer_id
        lead.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return lead

    # ── Opportunities ────────────────────────────────────────

    @staticmethod
    def list_opportunities(tenant_id, stage=None, assigned_to=None,
                           search=None, page=1, per_page=50):
        q = Opportunity.query.filter_by(tenant_id=tenant_id)
        if stage:
            q = q.filter_by(stage=stage)
        if assigned_to:
            q = q.filter_by(assigned_to=assigned_to)
        if search:
            like = f'%{search}%'
            q = q.filter(Opportunity.title.ilike(like))
        total = q.count()
        opps = q.order_by(Opportunity.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return opps, total

    @staticmethod
    def get_opportunity(tenant_id, opp_id):
        return Opportunity.query.filter_by(id=opp_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_opportunity(tenant_id, data):
        title = data.get('title', '').strip()
        if not title:
            raise ValueError('Title is required')
        opp = Opportunity(
            tenant_id=tenant_id, title=title,
            lead_id=data.get('lead_id'), customer_id=data.get('customer_id'),
            value=data.get('value', 0), currency=data.get('currency', 'USD'),
            stage=data.get('stage', 'prospecting'),
            probability=data.get('probability', 10),
            expected_close_date=data.get('expected_close_date'),
            assigned_to=data.get('assigned_to'),
            notes=data.get('notes'),
        )
        db.session.add(opp)
        db.session.commit()
        return opp

    @staticmethod
    def update_opportunity(tenant_id, opp_id, data):
        opp = Opportunity.query.filter_by(id=opp_id, tenant_id=tenant_id).first()
        if not opp:
            return None
        for f in ['title', 'lead_id', 'customer_id', 'value', 'currency',
                   'stage', 'probability', 'expected_close_date',
                   'assigned_to', 'notes']:
            if f in data:
                setattr(opp, f, data[f])
        opp.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return opp

    @staticmethod
    def delete_opportunity(tenant_id, opp_id):
        opp = Opportunity.query.filter_by(id=opp_id, tenant_id=tenant_id).first()
        if not opp:
            raise ValueError('Opportunity not found')
        db.session.delete(opp)
        db.session.commit()

    # ── Activities ───────────────────────────────────────────

    @staticmethod
    def list_activities(tenant_id, lead_id=None, opportunity_id=None,
                        activity_type=None, page=1, per_page=50):
        q = CRMActivity.query.filter_by(tenant_id=tenant_id)
        if lead_id:
            q = q.filter_by(lead_id=lead_id)
        if opportunity_id:
            q = q.filter_by(opportunity_id=opportunity_id)
        if activity_type:
            q = q.filter_by(activity_type=activity_type)
        total = q.count()
        acts = q.order_by(CRMActivity.date.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return acts, total

    @staticmethod
    def create_activity(tenant_id, data, user_id=None):
        act = CRMActivity(
            tenant_id=tenant_id,
            activity_type=data.get('activity_type', 'note'),
            subject=data.get('subject', ''),
            description=data.get('description'),
            lead_id=data.get('lead_id'),
            opportunity_id=data.get('opportunity_id'),
            user_id=user_id,
        )
        if data.get('date'):
            act.date = data['date']
        db.session.add(act)
        db.session.commit()
        return act

    # ── Pipeline Stats ───────────────────────────────────────

    @staticmethod
    def pipeline_stats(tenant_id):
        """Pipeline summary by stage."""
        rows = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.coalesce(func.sum(Opportunity.value), 0).label('total_value'),
        ).filter_by(tenant_id=tenant_id)\
         .group_by(Opportunity.stage).all()
        stages = {}
        for r in rows:
            stages[r.stage] = {'count': r.count, 'total_value': round(r.total_value, 2)}
        return {
            'stages': stages,
            'total_leads': Lead.query.filter_by(tenant_id=tenant_id).count(),
            'total_opportunities': Opportunity.query.filter_by(tenant_id=tenant_id).count(),
            'total_pipeline_value': round(sum(s['total_value'] for s in stages.values()), 2),
        }

    @staticmethod
    def get_stats(tenant_id):
        return CRMService.pipeline_stats(tenant_id)
