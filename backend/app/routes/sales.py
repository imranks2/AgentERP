"""Sales module API routes – Customers, Quotations, Invoices, Payments."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.utils.decorators import tenant_required
from app.services.sales_service import SalesService

sales_bp = Blueprint('sales', __name__)


def _module_check(tenant_id):
    from app.services.module_service import ModuleService
    if not ModuleService.is_module_enabled(tenant_id, 'sales'):
        return jsonify({'error': 'Sales module not enabled'}), 403
    return None


# ── Customers ────────────────────────────────────────────────

@sales_bp.route('/customers', methods=['GET'])
@jwt_required()
@tenant_required
def list_customers():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    customers, total = SalesService.list_customers(
        tenant_id,
        search=request.args.get('search'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify({
        'customers': [c.to_dict() for c in customers],
        'total': total,
    })


@sales_bp.route('/customers/<cust_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_customer(cust_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    cust = SalesService.get_customer(tenant_id, cust_id)
    if not cust:
        return jsonify({'error': 'Customer not found'}), 404
    return jsonify({'customer': cust.to_dict()})


@sales_bp.route('/customers', methods=['POST'])
@jwt_required()
@tenant_required
def create_customer():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        cust = SalesService.create_customer(tenant_id, request.get_json() or {})
        return jsonify({'customer': cust.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@sales_bp.route('/customers/<cust_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_customer(cust_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    cust = SalesService.update_customer(tenant_id, cust_id, request.get_json() or {})
    if not cust:
        return jsonify({'error': 'Customer not found'}), 404
    return jsonify({'customer': cust.to_dict()})


# ── Quotations ───────────────────────────────────────────────

@sales_bp.route('/quotations', methods=['GET'])
@jwt_required()
@tenant_required
def list_quotations():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    quotations, total = SalesService.list_quotations(
        tenant_id,
        status=request.args.get('status'),
        customer_id=request.args.get('customer_id'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify({
        'quotations': [q.to_dict() for q in quotations],
        'total': total,
    })


@sales_bp.route('/quotations/<quote_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_quotation(quote_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    quote = SalesService.get_quotation(tenant_id, quote_id)
    if not quote:
        return jsonify({'error': 'Quotation not found'}), 404
    return jsonify({'quotation': quote.to_dict()})


@sales_bp.route('/quotations', methods=['POST'])
@jwt_required()
@tenant_required
def create_quotation():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    user_id = get_jwt_identity()
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        quote = SalesService.create_quotation(
            tenant_id, request.get_json() or {}, user_id=user_id)
        return jsonify({'quotation': quote.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@sales_bp.route('/quotations/<quote_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_quotation(quote_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        quote = SalesService.update_quotation(
            tenant_id, quote_id, request.get_json() or {})
        if not quote:
            return jsonify({'error': 'Quotation not found'}), 404
        return jsonify({'quotation': quote.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@sales_bp.route('/quotations/<quote_id>/convert', methods=['POST'])
@jwt_required()
@tenant_required
def convert_quotation(quote_id):
    """Convert quotation to invoice – key integration endpoint."""
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    user_id = get_jwt_identity()
    err = _module_check(tenant_id)
    if err:
        return err
    data = request.get_json() or {}
    try:
        invoice = SalesService.convert_quotation_to_invoice(
            tenant_id, quote_id, user_id=user_id,
            warehouse_id=data.get('warehouse_id'))
        return jsonify({
            'message': 'Quotation converted to invoice',
            'invoice': invoice.to_dict(),
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Invoices ─────────────────────────────────────────────────

@sales_bp.route('/invoices', methods=['GET'])
@jwt_required()
@tenant_required
def list_invoices():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    invoices, total = SalesService.list_invoices(
        tenant_id,
        status=request.args.get('status'),
        customer_id=request.args.get('customer_id'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify({
        'invoices': [i.to_dict() for i in invoices],
        'total': total,
    })


@sales_bp.route('/invoices/<inv_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_invoice(inv_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    invoice = SalesService.get_invoice(tenant_id, inv_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    return jsonify({'invoice': invoice.to_dict()})


@sales_bp.route('/invoices', methods=['POST'])
@jwt_required()
@tenant_required
def create_invoice():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    user_id = get_jwt_identity()
    err = _module_check(tenant_id)
    if err:
        return err
    data = request.get_json() or {}
    try:
        invoice = SalesService.create_invoice(
            tenant_id, data, user_id=user_id,
            warehouse_id=data.get('warehouse_id'))
        return jsonify({'invoice': invoice.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@sales_bp.route('/invoices/<inv_id>/status', methods=['PUT'])
@jwt_required()
@tenant_required
def update_invoice_status(inv_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    data = request.get_json() or {}
    try:
        invoice = SalesService.update_invoice_status(
            tenant_id, inv_id, data.get('status'))
        return jsonify({'invoice': invoice.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Payments ─────────────────────────────────────────────────

@sales_bp.route('/invoices/<inv_id>/payments', methods=['GET'])
@jwt_required()
@tenant_required
def list_payments(inv_id):
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    payments, total = SalesService.list_payments(tenant_id, invoice_id=inv_id)
    return jsonify({
        'payments': [p.to_dict() for p in payments],
        'total': total,
    })


@sales_bp.route('/invoices/<inv_id>/payments', methods=['POST'])
@jwt_required()
@tenant_required
def record_payment(inv_id):
    """Record payment against invoice – auto-updates invoice status."""
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    user_id = get_jwt_identity()
    err = _module_check(tenant_id)
    if err:
        return err
    try:
        payment, invoice = SalesService.record_payment(
            tenant_id, inv_id, request.get_json() or {}, user_id=user_id)
        return jsonify({
            'payment': payment.to_dict(),
            'invoice': invoice.to_dict(),
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Stats ────────────────────────────────────────────────────

@sales_bp.route('/stats', methods=['GET'])
@jwt_required()
@tenant_required
def sales_stats():
    claims = get_jwt()
    tenant_id = claims['tenant_id']
    err = _module_check(tenant_id)
    if err:
        return err
    stats = SalesService.get_sales_stats(tenant_id)
    return jsonify({'stats': stats})
