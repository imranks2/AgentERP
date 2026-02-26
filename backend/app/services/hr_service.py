"""HR service – Employees, Leave, Payroll, Attendance."""
from datetime import datetime, timezone, date
from sqlalchemy import func
from app import db
from app.models.hr import (
    Employee, LeaveType, LeaveRequest, PayrollRun, PaySlip, Attendance,
)


def _parse_date(val):
    """Convert string or date to date object."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    return date.fromisoformat(str(val)[:10])


class HRService:

    # ── Employees ────────────────────────────────────────────

    @staticmethod
    def list_employees(tenant_id, status=None, department_id=None,
                       employment_type=None, search=None, page=1, per_page=50):
        q = Employee.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        if department_id:
            q = q.filter_by(department_id=department_id)
        if employment_type:
            q = q.filter_by(employment_type=employment_type)
        if search:
            like = f'%{search}%'
            q = q.filter(db.or_(
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                Employee.employee_number.ilike(like),
                Employee.email.ilike(like),
            ))
        total = q.count()
        employees = q.order_by(Employee.last_name, Employee.first_name)\
            .offset((page - 1) * per_page).limit(per_page).all()
        return employees, total

    @staticmethod
    def get_employee(tenant_id, emp_id):
        return Employee.query.filter_by(id=emp_id, tenant_id=tenant_id).first()

    @staticmethod
    def _next_employee_number(tenant_id):
        last = Employee.query.filter_by(tenant_id=tenant_id)\
            .order_by(Employee.created_at.desc()).first()
        if last:
            try:
                seq = int(last.employee_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'EMP-{seq:05d}'

    @staticmethod
    def create_employee(tenant_id, data):
        first = data.get('first_name', '').strip()
        last = data.get('last_name', '').strip()
        if not first or not last:
            raise ValueError('first_name and last_name are required')
        hire_date = data.get('hire_date')
        if not hire_date:
            raise ValueError('hire_date is required')
        emp_number = data.get('employee_number') or HRService._next_employee_number(tenant_id)
        emp = Employee(
            tenant_id=tenant_id, employee_number=emp_number,
            first_name=first, last_name=last,
            email=data.get('email'), phone=data.get('phone'),
            hire_date=_parse_date(hire_date), department_id=data.get('department_id'),
            job_title=data.get('job_title'),
            employment_type=data.get('employment_type', 'full_time'),
            salary=data.get('salary', 0), currency=data.get('currency', 'USD'),
            user_id=data.get('user_id'),
        )
        db.session.add(emp)
        db.session.commit()
        return emp

    @staticmethod
    def update_employee(tenant_id, emp_id, data):
        emp = Employee.query.filter_by(id=emp_id, tenant_id=tenant_id).first()
        if not emp:
            return None
        date_fields = {'hire_date', 'termination_date'}
        for f in ['first_name', 'last_name', 'email', 'phone', 'hire_date',
                   'termination_date', 'department_id', 'job_title',
                   'employment_type', 'status', 'salary', 'currency', 'user_id']:
            if f in data:
                val = _parse_date(data[f]) if f in date_fields else data[f]
                setattr(emp, f, val)
        emp.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return emp

    @staticmethod
    def terminate_employee(tenant_id, emp_id, termination_date=None):
        emp = Employee.query.filter_by(id=emp_id, tenant_id=tenant_id).first()
        if not emp:
            raise ValueError('Employee not found')
        emp.status = 'terminated'
        emp.termination_date = _parse_date(termination_date) or date.today()
        emp.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return emp

    # ── Leave Types ──────────────────────────────────────────

    @staticmethod
    def list_leave_types(tenant_id):
        return LeaveType.query.filter_by(tenant_id=tenant_id).order_by(LeaveType.name).all()

    @staticmethod
    def create_leave_type(tenant_id, data):
        lt = LeaveType(
            tenant_id=tenant_id, name=data['name'], code=data['code'],
            default_days=data.get('default_days', 0),
            is_paid=data.get('is_paid', True),
        )
        db.session.add(lt)
        db.session.commit()
        return lt

    # ── Leave Requests ───────────────────────────────────────

    @staticmethod
    def list_leave_requests(tenant_id, employee_id=None, status=None,
                            page=1, per_page=50):
        q = LeaveRequest.query.filter_by(tenant_id=tenant_id)
        if employee_id:
            q = q.filter_by(employee_id=employee_id)
        if status:
            q = q.filter_by(status=status)
        total = q.count()
        reqs = q.order_by(LeaveRequest.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return reqs, total

    @staticmethod
    def create_leave_request(tenant_id, data):
        lr = LeaveRequest(
            tenant_id=tenant_id,
            employee_id=data['employee_id'],
            leave_type_id=data['leave_type_id'],
            start_date=_parse_date(data['start_date']), end_date=_parse_date(data['end_date']),
            days=data['days'], reason=data.get('reason'),
        )
        db.session.add(lr)
        db.session.commit()
        return lr

    @staticmethod
    def approve_leave(tenant_id, request_id, approver_id):
        lr = LeaveRequest.query.filter_by(id=request_id, tenant_id=tenant_id).first()
        if not lr:
            raise ValueError('Leave request not found')
        lr.status = 'approved'
        lr.approved_by = approver_id
        lr.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return lr

    @staticmethod
    def reject_leave(tenant_id, request_id):
        lr = LeaveRequest.query.filter_by(id=request_id, tenant_id=tenant_id).first()
        if not lr:
            raise ValueError('Leave request not found')
        lr.status = 'rejected'
        lr.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return lr

    # ── Payroll ──────────────────────────────────────────────

    @staticmethod
    def list_payroll_runs(tenant_id, status=None, page=1, per_page=50):
        q = PayrollRun.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        total = q.count()
        runs = q.order_by(PayrollRun.period_start.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return runs, total

    @staticmethod
    def get_payroll_run(tenant_id, run_id):
        return PayrollRun.query.filter_by(id=run_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_payroll_run(tenant_id, data, user_id=None):
        run = PayrollRun(
            tenant_id=tenant_id,
            period_start=_parse_date(data['period_start']), period_end=_parse_date(data['period_end']),
        )
        db.session.add(run)
        db.session.flush()
        # Auto-generate pay slips for all active employees
        employees = Employee.query.filter_by(tenant_id=tenant_id, status='active').all()
        total_gross = 0
        total_net = 0
        for emp in employees:
            monthly_salary = round(emp.salary / 12, 2) if emp.salary else 0
            deductions = round(monthly_salary * 0.2, 2)  # simple 20% deduction placeholder
            net = round(monthly_salary - deductions, 2)
            ps = PaySlip(
                tenant_id=tenant_id, payroll_run_id=run.id,
                employee_id=emp.id, gross_pay=monthly_salary,
                deductions=deductions, net_pay=net,
                details={'basic': monthly_salary, 'tax': deductions},
            )
            db.session.add(ps)
            total_gross += monthly_salary
            total_net += net
        run.total_gross = round(total_gross, 2)
        run.total_deductions = round(total_gross - total_net, 2)
        run.total_net = round(total_net, 2)
        db.session.commit()
        return run

    @staticmethod
    def process_payroll(tenant_id, run_id, user_id=None):
        run = PayrollRun.query.filter_by(id=run_id, tenant_id=tenant_id).first()
        if not run:
            raise ValueError('Payroll run not found')
        if run.status != 'draft':
            raise ValueError('Only draft payroll runs can be processed')
        run.status = 'completed'
        run.processed_by = user_id
        run.processed_at = datetime.now(timezone.utc)
        db.session.commit()
        return run

    # ── Attendance ───────────────────────────────────────────

    @staticmethod
    def list_attendance(tenant_id, employee_id=None, date_from=None, date_to=None,
                        page=1, per_page=50):
        q = Attendance.query.filter_by(tenant_id=tenant_id)
        if employee_id:
            q = q.filter_by(employee_id=employee_id)
        if date_from:
            q = q.filter(Attendance.date >= date_from)
        if date_to:
            q = q.filter(Attendance.date <= date_to)
        total = q.count()
        records = q.order_by(Attendance.date.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return records, total

    @staticmethod
    def record_attendance(tenant_id, data):
        att = Attendance(
            tenant_id=tenant_id, employee_id=data['employee_id'],
            date=_parse_date(data['date']), check_in=data.get('check_in'),
            check_out=data.get('check_out'),
            status=data.get('status', 'present'),
            notes=data.get('notes'),
        )
        db.session.add(att)
        db.session.commit()
        return att

    @staticmethod
    def update_attendance(tenant_id, att_id, data):
        att = Attendance.query.filter_by(id=att_id, tenant_id=tenant_id).first()
        if not att:
            return None
        for f in ['check_in', 'check_out', 'status', 'notes']:
            if f in data:
                setattr(att, f, data[f])
        db.session.commit()
        return att

    # ── Stats ────────────────────────────────────────────────

    @staticmethod
    def get_stats(tenant_id):
        total_emp = Employee.query.filter_by(tenant_id=tenant_id).count()
        active_emp = Employee.query.filter_by(tenant_id=tenant_id, status='active').count()
        pending_leaves = LeaveRequest.query.filter_by(
            tenant_id=tenant_id, status='pending').count()
        today = date.today()
        present_today = Attendance.query.filter_by(
            tenant_id=tenant_id, date=today, status='present').count()
        return {
            'total_employees': total_emp,
            'active_employees': active_emp,
            'on_leave': total_emp - active_emp,
            'pending_leave_requests': pending_leaves,
            'present_today': present_today,
        }
