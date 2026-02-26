"""Accounting routes – Phase 8.

Endpoints for Chart of Accounts, Journal Entries, Fiscal Years,
Tax Rates, Currencies, and financial reports.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.utils.decorators import tenant_required
from app.services.accounting_service import AccountingService

accounting_bp = Blueprint('accounting', __name__)


def _tid():
    return get_jwt()['tenant_id']


def _uid():
    return get_jwt_identity()


# ── Chart of Accounts ────────────────────────────────────────

@accounting_bp.route('/accounts', methods=['GET'])
@jwt_required()
@tenant_required
def list_accounts():
    accts, total = AccountingService.list_accounts(
        _tid(),
        account_type=request.args.get('account_type'),
        parent_id=request.args.get('parent_id'),
        search=request.args.get('search'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(accounts=[a.to_dict() for a in accts], total=total)


@accounting_bp.route('/accounts', methods=['POST'])
@jwt_required()
@tenant_required
def create_account():
    try:
        acct = AccountingService.create_account(_tid(), request.json)
        return jsonify(acct.to_dict()), 201
    except ValueError as e:
        return jsonify(error=str(e)), 400


@accounting_bp.route('/accounts/<account_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_account(account_id):
    acct = AccountingService.get_account(_tid(), account_id)
    if not acct:
        return jsonify(error='Account not found'), 404
    return jsonify(acct.to_dict())


@accounting_bp.route('/accounts/<account_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_account(account_id):
    acct = AccountingService.update_account(_tid(), account_id, request.json)
    if not acct:
        return jsonify(error='Account not found'), 404
    return jsonify(acct.to_dict())


@accounting_bp.route('/accounts/<account_id>', methods=['DELETE'])
@jwt_required()
@tenant_required
def delete_account(account_id):
    try:
        AccountingService.delete_account(_tid(), account_id)
        return jsonify(message='Account deleted'), 200
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ── Fiscal Years ─────────────────────────────────────────────

@accounting_bp.route('/fiscal-years', methods=['GET'])
@jwt_required()
@tenant_required
def list_fiscal_years():
    fys = AccountingService.list_fiscal_years(_tid())
    return jsonify(fiscal_years=[f.to_dict() for f in fys])


@accounting_bp.route('/fiscal-years', methods=['POST'])
@jwt_required()
@tenant_required
def create_fiscal_year():
    try:
        fy = AccountingService.create_fiscal_year(_tid(), request.json)
        return jsonify(fy.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400


@accounting_bp.route('/fiscal-years/<fy_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_fiscal_year(fy_id):
    fy = AccountingService.get_fiscal_year(_tid(), fy_id)
    if not fy:
        return jsonify(error='Fiscal year not found'), 404
    result = fy.to_dict()
    result['periods'] = [p.to_dict() for p in fy.periods.order_by('period_number').all()]
    return jsonify(result)


@accounting_bp.route('/fiscal-years/<fy_id>/close', methods=['POST'])
@jwt_required()
@tenant_required
def close_fiscal_year(fy_id):
    try:
        fy = AccountingService.close_fiscal_year(_tid(), fy_id)
        return jsonify(fy.to_dict())
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ── Journal Entries ──────────────────────────────────────────

@accounting_bp.route('/journal-entries', methods=['GET'])
@jwt_required()
@tenant_required
def list_journal_entries():
    entries, total = AccountingService.list_journal_entries(
        _tid(),
        status=request.args.get('status'),
        reference_type=request.args.get('reference_type'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(entries=[e.to_dict() for e in entries], total=total)


@accounting_bp.route('/journal-entries', methods=['POST'])
@jwt_required()
@tenant_required
def create_journal_entry():
    try:
        je = AccountingService.create_journal_entry(
            _tid(), request.json, user_id=_uid())
        return jsonify(je.to_dict()), 201
    except ValueError as e:
        return jsonify(error=str(e)), 400


@accounting_bp.route('/journal-entries/<entry_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_journal_entry(entry_id):
    je = AccountingService.get_journal_entry(_tid(), entry_id)
    if not je:
        return jsonify(error='Journal entry not found'), 404
    return jsonify(je.to_dict())


@accounting_bp.route('/journal-entries/<entry_id>/post', methods=['POST'])
@jwt_required()
@tenant_required
def post_journal_entry(entry_id):
    try:
        je = AccountingService.post_journal_entry(_tid(), entry_id)
        return jsonify(je.to_dict())
    except ValueError as e:
        return jsonify(error=str(e)), 400


@accounting_bp.route('/journal-entries/<entry_id>/reverse', methods=['POST'])
@jwt_required()
@tenant_required
def reverse_journal_entry(entry_id):
    try:
        reversal = AccountingService.reverse_journal_entry(
            _tid(), entry_id, user_id=_uid())
        return jsonify(reversal.to_dict())
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ── Tax Rates ────────────────────────────────────────────────

@accounting_bp.route('/tax-rates', methods=['GET'])
@jwt_required()
@tenant_required
def list_tax_rates():
    rates = AccountingService.list_tax_rates(_tid())
    return jsonify(tax_rates=[r.to_dict() for r in rates])


@accounting_bp.route('/tax-rates', methods=['POST'])
@jwt_required()
@tenant_required
def create_tax_rate():
    try:
        tr = AccountingService.create_tax_rate(_tid(), request.json)
        return jsonify(tr.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400


@accounting_bp.route('/tax-rates/<tax_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_tax_rate(tax_id):
    tr = AccountingService.update_tax_rate(_tid(), tax_id, request.json)
    if not tr:
        return jsonify(error='Tax rate not found'), 404
    return jsonify(tr.to_dict())


# ── Currencies ───────────────────────────────────────────────

@accounting_bp.route('/currencies', methods=['GET'])
@jwt_required()
@tenant_required
def list_currencies():
    currencies = AccountingService.list_currencies(_tid())
    return jsonify(currencies=[c.to_dict() for c in currencies])


@accounting_bp.route('/currencies', methods=['POST'])
@jwt_required()
@tenant_required
def create_currency():
    try:
        cr = AccountingService.create_currency(_tid(), request.json)
        return jsonify(cr.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400


@accounting_bp.route('/currencies/<currency_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_currency(currency_id):
    cr = AccountingService.update_currency(_tid(), currency_id, request.json)
    if not cr:
        return jsonify(error='Currency not found'), 404
    return jsonify(cr.to_dict())


# ── Reports ──────────────────────────────────────────────────

@accounting_bp.route('/reports/trial-balance', methods=['GET'])
@jwt_required()
@tenant_required
def trial_balance():
    as_of = request.args.get('as_of')
    tb = AccountingService.trial_balance(_tid(), as_of=as_of)
    return jsonify(trial_balance=tb)


@accounting_bp.route('/reports/profit-loss', methods=['GET'])
@jwt_required()
@tenant_required
def profit_and_loss():
    pl = AccountingService.profit_and_loss(
        _tid(),
        start_date=request.args.get('start_date'),
        end_date=request.args.get('end_date'),
    )
    return jsonify(pl)


@accounting_bp.route('/reports/balance-sheet', methods=['GET'])
@jwt_required()
@tenant_required
def balance_sheet():
    bs = AccountingService.balance_sheet(
        _tid(), as_of=request.args.get('as_of'))
    return jsonify(bs)


@accounting_bp.route('/stats', methods=['GET'])
@jwt_required()
@tenant_required
def accounting_stats():
    return jsonify(AccountingService.get_stats(_tid()))
