"""HR models – Phase 8.

Employees, leave management, payroll, and attendance tracking.
"""
import uuid
from datetime import datetime, timezone
from app import db


def _uuid():
    return str(uuid.uuid4())


class Employee(db.Model):
    """Employee record linked to a user account."""
    __tablename__ = 'employees'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    employee_number = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    hire_date = db.Column(db.Date, nullable=False)
    termination_date = db.Column(db.Date, nullable=True)
    department_id = db.Column(db.String(36), db.ForeignKey('organisation_units.id'), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    employment_type = db.Column(db.String(20), default='full_time')  # full_time, part_time, contract, intern
    status = db.Column(db.String(20), default='active')  # active, on_leave, terminated
    salary = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy='dynamic')
    pay_slips = db.relationship('PaySlip', backref='employee', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='employee', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'employee_number', name='uq_emp_number'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id, 'user_id': self.user_id,
            'employee_number': self.employee_number,
            'first_name': self.first_name, 'last_name': self.last_name,
            'email': self.email, 'phone': self.phone,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'termination_date': self.termination_date.isoformat() if self.termination_date else None,
            'department_id': self.department_id, 'job_title': self.job_title,
            'employment_type': self.employment_type, 'status': self.status,
            'salary': self.salary, 'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class LeaveType(db.Model):
    """Leave category (annual, sick, etc.)."""
    __tablename__ = 'leave_types'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    name = db.Column(db.String(60), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    default_days = db.Column(db.Float, default=0)
    is_paid = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'code', name='uq_leave_type_code'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'name': self.name, 'code': self.code,
            'default_days': self.default_days, 'is_paid': self.is_paid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class LeaveRequest(db.Model):
    """Employee leave application."""
    __tablename__ = 'leave_requests'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    employee_id = db.Column(db.String(36), db.ForeignKey('employees.id'), nullable=False)
    leave_type_id = db.Column(db.String(36), db.ForeignKey('leave_types.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, cancelled
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    leave_type = db.relationship('LeaveType', backref='requests')

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'employee_id': self.employee_id, 'leave_type_id': self.leave_type_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'days': self.days, 'reason': self.reason,
            'status': self.status, 'approved_by': self.approved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PayrollRun(db.Model):
    """Monthly/periodic payroll batch."""
    __tablename__ = 'payroll_runs'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, processing, completed, cancelled
    total_gross = db.Column(db.Float, default=0)
    total_deductions = db.Column(db.Float, default=0)
    total_net = db.Column(db.Float, default=0)
    processed_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    pay_slips = db.relationship('PaySlip', backref='payroll_run', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'status': self.status, 'total_gross': self.total_gross,
            'total_deductions': self.total_deductions, 'total_net': self.total_net,
            'processed_by': self.processed_by,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PaySlip(db.Model):
    """Individual employee pay slip within a payroll run."""
    __tablename__ = 'pay_slips'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    payroll_run_id = db.Column(db.String(36), db.ForeignKey('payroll_runs.id'), nullable=False)
    employee_id = db.Column(db.String(36), db.ForeignKey('employees.id'), nullable=False)
    gross_pay = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    net_pay = db.Column(db.Float, default=0)
    details = db.Column(db.JSON, default=dict)  # breakdown: {basic, allowances, taxes, ...}
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'payroll_run_id': self.payroll_run_id, 'employee_id': self.employee_id,
            'gross_pay': self.gross_pay, 'deductions': self.deductions,
            'net_pay': self.net_pay, 'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Attendance(db.Model):
    """Daily attendance record."""
    __tablename__ = 'attendances'

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    employee_id = db.Column(db.String(36), db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='present')  # present, absent, half_day, remote
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'employee_id', 'date', name='uq_attendance_day'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'employee_id': self.employee_id,
            'date': self.date.isoformat() if self.date else None,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'status': self.status, 'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
