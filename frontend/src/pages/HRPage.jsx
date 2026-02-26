import React, { useState, useEffect, useCallback } from 'react';
import { hrAPI } from '../services/api';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import TabBar from '../components/TabBar';
import StatCards from '../components/StatCards';
import Alert from '../components/Alert';
import PageHeader from '../components/PageHeader';
import {
  UserCheck, Plus, Edit3, Clock,
  CalendarOff, DollarSign, CheckCircle, XCircle,
} from 'lucide-react';
import '../styles/erp.css';

function HRPage() {
  const [tab, setTab] = useState('employees');
  const [employees, setEmployees] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [payrollRuns, setPayrollRuns] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [formType, setFormType] = useState('employee');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [empRes, ltRes, lrRes, prRes, attRes, statRes] = await Promise.all([
        hrAPI.listEmployees({ search }).catch(() => ({ data: { employees: [] } })),
        hrAPI.listLeaveTypes().catch(() => ({ data: { leave_types: [] } })),
        hrAPI.listLeaveRequests({}).catch(() => ({ data: { leave_requests: [] } })),
        hrAPI.listPayrollRuns({}).catch(() => ({ data: { payroll_runs: [] } })),
        hrAPI.listAttendance({}).catch(() => ({ data: { attendance: [] } })),
        hrAPI.stats().catch(() => ({ data: {} })),
      ]);
      setEmployees(empRes.data.employees || []);
      setLeaveTypes(ltRes.data.leave_types || []);
      setLeaveRequests(lrRes.data.leave_requests || []);
      setPayrollRuns(prRes.data.payroll_runs || []);
      setAttendance(attRes.data.attendance || []);
      setStats(statRes.data || {});
    } catch {
      setError('Failed to load HR data');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { loadData(); }, [loadData]);

  /* ── Employee form ─────────────────────────── */
  const empFields = [
    { name: 'first_name', label: 'First Name', type: 'text', required: true },
    { name: 'last_name', label: 'Last Name', type: 'text', required: true },
    { name: 'email', label: 'Email', type: 'email' },
    { name: 'phone', label: 'Phone', type: 'text' },
    { name: 'hire_date', label: 'Hire Date', type: 'date', required: true },
    { name: 'job_title', label: 'Job Title', type: 'text' },
    { name: 'employment_type', label: 'Type', type: 'select', options: [
      { value: 'full_time', label: 'Full Time' }, { value: 'part_time', label: 'Part Time' },
      { value: 'contract', label: 'Contract' }, { value: 'intern', label: 'Intern' },
    ]},
    { name: 'salary', label: 'Annual Salary', type: 'number' },
  ];

  const handleSaveEmployee = async (formData) => {
    try {
      if (editItem) { await hrAPI.updateEmployee(editItem.id, formData); setSuccess('Employee updated'); }
      else { await hrAPI.createEmployee(formData); setSuccess('Employee created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Failed to save employee'); }
  };

  const handleApproveLeave = async (lr) => {
    try { await hrAPI.approveLeave(lr.id); setSuccess('Leave approved'); loadData(); }
    catch (err) { setError(err.response?.data?.error || 'Approve failed'); }
  };

  const handleRejectLeave = async (lr) => {
    try { await hrAPI.rejectLeave(lr.id); setSuccess('Leave rejected'); loadData(); }
    catch (err) { setError(err.response?.data?.error || 'Reject failed'); }
  };

  const handleProcessPayroll = async (run) => {
    try { await hrAPI.processPayroll(run.id); setSuccess('Payroll processed'); loadData(); }
    catch (err) { setError(err.response?.data?.error || 'Process failed'); }
  };

  const openNew = (type) => { setFormType(type); setEditItem(null); setShowForm(true); };

  const tabs = [
    { key: 'employees', label: 'Employees', icon: <UserCheck size={16} /> },
    { key: 'leave', label: 'Leave', icon: <CalendarOff size={16} /> },
    { key: 'payroll', label: 'Payroll', icon: <DollarSign size={16} /> },
    { key: 'attendance', label: 'Attendance', icon: <Clock size={16} /> },
  ];

  const statusBadge = (s) => {
    const m = { active: 'badge-success', on_leave: 'badge-warning', terminated: 'badge-danger',
      pending: 'badge-warning', approved: 'badge-success', rejected: 'badge-danger',
      draft: 'badge-secondary', completed: 'badge-success', present: 'badge-success',
      absent: 'badge-danger', half_day: 'badge-warning', remote: 'badge-info' };
    return m[s] || 'badge-secondary';
  };

  const empCols = [
    { key: 'employee_number', label: 'ID', sortable: true },
    { key: 'first_name', label: 'First', sortable: true },
    { key: 'last_name', label: 'Last', sortable: true },
    { key: 'job_title', label: 'Title' },
    { key: 'employment_type', label: 'Type', render: (v) => v?.replace('_', ' ') },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
    { key: 'actions', label: '', render: (_, row) => (
      <div className="action-btns">
        <button className="btn btn-sm" onClick={() => { setFormType('employee'); setEditItem(row); setShowForm(true); }}><Edit3 size={14} /></button>
      </div>
    )},
  ];

  const leaveCols = [
    { key: 'employee_id', label: 'Employee' },
    { key: 'start_date', label: 'Start' }, { key: 'end_date', label: 'End' },
    { key: 'days', label: 'Days' },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
    { key: 'actions', label: '', render: (_, row) => row.status === 'pending' ? (
      <div className="action-btns">
        <button className="btn btn-sm btn-success" onClick={() => handleApproveLeave(row)} title="Approve"><CheckCircle size={14} /></button>
        <button className="btn btn-sm btn-danger" onClick={() => handleRejectLeave(row)} title="Reject"><XCircle size={14} /></button>
      </div>
    ) : null },
  ];

  const payrollCols = [
    { key: 'period_start', label: 'Start' }, { key: 'period_end', label: 'End' },
    { key: 'total_gross', label: 'Gross', render: (v) => `$${(v || 0).toLocaleString()}` },
    { key: 'total_net', label: 'Net', render: (v) => `$${(v || 0).toLocaleString()}` },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
    { key: 'actions', label: '', render: (_, row) => row.status === 'draft' ? (
      <button className="btn btn-sm btn-success" onClick={() => handleProcessPayroll(row)}>Process</button>
    ) : null },
  ];

  const attCols = [
    { key: 'employee_id', label: 'Employee' },
    { key: 'date', label: 'Date', sortable: true },
    { key: 'check_in', label: 'In', render: (v) => v ? new Date(v).toLocaleTimeString() : '—' },
    { key: 'check_out', label: 'Out', render: (v) => v ? new Date(v).toLocaleTimeString() : '—' },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
  ];

  return (
    <div className="erp-page">
      <PageHeader title="Human Resources" icon={<UserCheck />}
        action={tab === 'employees' ? { label: 'New Employee', icon: <Plus size={16} />, onClick: () => openNew('employee') } : null}
      />
      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {stats && (
        <StatCards cards={[
          { label: 'Total Employees', value: stats.total_employees || 0 },
          { label: 'Active', value: stats.active_employees || 0 },
          { label: 'Pending Leaves', value: stats.pending_leave_requests || 0 },
          { label: 'Present Today', value: stats.present_today || 0 },
        ]} />
      )}

      <TabBar tabs={tabs} active={tab} onChange={setTab} />

      {tab === 'employees' && (
        <>
          <div className="toolbar"><input className="search-input" placeholder="Search employees…" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
          <DataTable columns={empCols} data={employees} loading={loading} emptyMessage="No employees yet" />
        </>
      )}

      {tab === 'leave' && (
        <DataTable columns={leaveCols} data={leaveRequests} loading={loading} emptyMessage="No leave requests" />
      )}

      {tab === 'payroll' && (
        <DataTable columns={payrollCols} data={payrollRuns} loading={loading} emptyMessage="No payroll runs" />
      )}

      {tab === 'attendance' && (
        <DataTable columns={attCols} data={attendance} loading={loading} emptyMessage="No attendance records" />
      )}

      {showForm && formType === 'employee' && (
        <Modal title={editItem ? 'Edit Employee' : 'New Employee'} onClose={() => { setShowForm(false); setEditItem(null); }}>
          <DynamicForm fields={empFields} initialValues={editItem || {}} onSubmit={handleSaveEmployee} submitLabel={editItem ? 'Update' : 'Create'} />
        </Modal>
      )}
    </div>
  );
}

export default HRPage;
