"""HR routes – Phase 8.

Endpoints for Employees, Leave, Payroll, and Attendance.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.utils.decorators import tenant_required
from app.services.hr_service import HRService

hr_bp = Blueprint('hr', __name__)


def _tid():
    return get_jwt()['tenant_id']


def _uid():
    return get_jwt_identity()


# ── Employees ────────────────────────────────────────────────

@hr_bp.route('/employees', methods=['GET'])
@jwt_required()
@tenant_required
def list_employees():
    emps, total = HRService.list_employees(
        _tid(),
        status=request.args.get('status'),
        department_id=request.args.get('department_id'),
        employment_type=request.args.get('employment_type'),
        search=request.args.get('search'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(employees=[e.to_dict() for e in emps], total=total)


@hr_bp.route('/employees', methods=['POST'])
@jwt_required()
@tenant_required
def create_employee():
    try:
        emp = HRService.create_employee(_tid(), request.json)
        return jsonify(emp.to_dict()), 201
    except ValueError as e:
        return jsonify(error=str(e)), 400


@hr_bp.route('/employees/<emp_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_employee(emp_id):
    emp = HRService.get_employee(_tid(), emp_id)
    if not emp:
        return jsonify(error='Employee not found'), 404
    return jsonify(emp.to_dict())


@hr_bp.route('/employees/<emp_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_employee(emp_id):
    emp = HRService.update_employee(_tid(), emp_id, request.json)
    if not emp:
        return jsonify(error='Employee not found'), 404
    return jsonify(emp.to_dict())


@hr_bp.route('/employees/<emp_id>/terminate', methods=['POST'])
@jwt_required()
@tenant_required
def terminate_employee(emp_id):
    try:
        emp = HRService.terminate_employee(
            _tid(), emp_id,
            termination_date=request.json.get('termination_date') if request.json else None,
        )
        return jsonify(emp.to_dict())
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ── Leave Types ──────────────────────────────────────────────

@hr_bp.route('/leave-types', methods=['GET'])
@jwt_required()
@tenant_required
def list_leave_types():
    types = HRService.list_leave_types(_tid())
    return jsonify(leave_types=[t.to_dict() for t in types])


@hr_bp.route('/leave-types', methods=['POST'])
@jwt_required()
@tenant_required
def create_leave_type():
    try:
        lt = HRService.create_leave_type(_tid(), request.json)
        return jsonify(lt.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400


# ── Leave Requests ───────────────────────────────────────────

@hr_bp.route('/leave-requests', methods=['GET'])
@jwt_required()
@tenant_required
def list_leave_requests():
    reqs, total = HRService.list_leave_requests(
        _tid(),
        employee_id=request.args.get('employee_id'),
        status=request.args.get('status'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(leave_requests=[r.to_dict() for r in reqs], total=total)


@hr_bp.route('/leave-requests', methods=['POST'])
@jwt_required()
@tenant_required
def create_leave_request():
    try:
        lr = HRService.create_leave_request(_tid(), request.json)
        return jsonify(lr.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400


@hr_bp.route('/leave-requests/<req_id>/approve', methods=['POST'])
@jwt_required()
@tenant_required
def approve_leave(req_id):
    try:
        lr = HRService.approve_leave(_tid(), req_id, _uid())
        return jsonify(lr.to_dict())
    except ValueError as e:
        return jsonify(error=str(e)), 400


@hr_bp.route('/leave-requests/<req_id>/reject', methods=['POST'])
@jwt_required()
@tenant_required
def reject_leave(req_id):
    try:
        lr = HRService.reject_leave(_tid(), req_id)
        return jsonify(lr.to_dict())
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ── Payroll ──────────────────────────────────────────────────

@hr_bp.route('/payroll-runs', methods=['GET'])
@jwt_required()
@tenant_required
def list_payroll_runs():
    runs, total = HRService.list_payroll_runs(
        _tid(),
        status=request.args.get('status'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(payroll_runs=[r.to_dict() for r in runs], total=total)


@hr_bp.route('/payroll-runs', methods=['POST'])
@jwt_required()
@tenant_required
def create_payroll_run():
    try:
        run = HRService.create_payroll_run(_tid(), request.json, user_id=_uid())
        return jsonify(run.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400


@hr_bp.route('/payroll-runs/<run_id>', methods=['GET'])
@jwt_required()
@tenant_required
def get_payroll_run(run_id):
    run = HRService.get_payroll_run(_tid(), run_id)
    if not run:
        return jsonify(error='Payroll run not found'), 404
    result = run.to_dict()
    result['pay_slips'] = [ps.to_dict() for ps in run.pay_slips.all()]
    return jsonify(result)


@hr_bp.route('/payroll-runs/<run_id>/process', methods=['POST'])
@jwt_required()
@tenant_required
def process_payroll(run_id):
    try:
        run = HRService.process_payroll(_tid(), run_id, user_id=_uid())
        return jsonify(run.to_dict())
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ── Attendance ───────────────────────────────────────────────

@hr_bp.route('/attendance', methods=['GET'])
@jwt_required()
@tenant_required
def list_attendance():
    records, total = HRService.list_attendance(
        _tid(),
        employee_id=request.args.get('employee_id'),
        date_from=request.args.get('date_from'),
        date_to=request.args.get('date_to'),
        page=int(request.args.get('page', 1)),
        per_page=int(request.args.get('per_page', 50)),
    )
    return jsonify(attendance=[r.to_dict() for r in records], total=total)


@hr_bp.route('/attendance', methods=['POST'])
@jwt_required()
@tenant_required
def record_attendance():
    try:
        att = HRService.record_attendance(_tid(), request.json)
        return jsonify(att.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400


@hr_bp.route('/attendance/<att_id>', methods=['PUT'])
@jwt_required()
@tenant_required
def update_attendance(att_id):
    att = HRService.update_attendance(_tid(), att_id, request.json)
    if not att:
        return jsonify(error='Attendance record not found'), 404
    return jsonify(att.to_dict())


# ── Stats ────────────────────────────────────────────────────

@hr_bp.route('/stats', methods=['GET'])
@jwt_required()
@tenant_required
def hr_stats():
    return jsonify(HRService.get_stats(_tid()))
