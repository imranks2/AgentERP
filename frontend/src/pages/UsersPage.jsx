import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../services/AuthContext';
import { usersAPI } from '../services/api';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import { useToast } from '../components/Toast';
import { UserPlus, Shield, ScrollText, RefreshCw } from 'lucide-react';

/* ── Invite user modal ─────────────────────────────── */
function InviteModal({ open, onClose, onInvited, roles }) {
  const [form, setForm] = useState({ email: '', first_name: '', last_name: '', role: 'user', password: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await usersAPI.invite(form);
      onInvited();
      onClose();
      setForm({ email: '', first_name: '', last_name: '', role: 'user', password: '' });
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to invite user');
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;
  return (
    <Modal title="Invite User" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        {error && <div className="form-error">{error}</div>}
        <div className="form-group">
          <label>Email *</label>
          <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>First Name *</label>
            <input required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </div>
          <div className="form-group">
            <label>Last Name *</label>
            <input required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Role</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {roles.map((r) => <option key={r.slug} value={r.slug}>{r.name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Temp Password</label>
            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Optional" />
          </div>
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Inviting…' : 'Send Invite'}</button>
        </div>
      </form>
    </Modal>
  );
}

/* ── Edit user modal ───────────────────────────────── */
function EditModal({ open, onClose, onSaved, user, roles }) {
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', role: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) setForm({ first_name: user.first_name, last_name: user.last_name, email: user.email, role: user.role });
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await usersAPI.update(user.id, form);
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update user');
    } finally {
      setSaving(false);
    }
  };

  if (!open || !user) return null;
  return (
    <Modal title="Edit User" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        {error && <div className="form-error">{error}</div>}
        <div className="form-row">
          <div className="form-group">
            <label>First Name</label>
            <input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </div>
          <div className="form-group">
            <label>Last Name</label>
            <input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </div>
        </div>
        <div className="form-group">
          <label>Email</label>
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <div className="form-group">
          <label>Role</label>
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            {roles.map((r) => <option key={r.slug} value={r.slug}>{r.name}</option>)}
          </select>
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
        </div>
      </form>
    </Modal>
  );
}

/* ── Main component ────────────────────────────────── */
export default function UsersPage() {
  const { hasRole } = useAuth();
  const toast = useToast();
  const [tab, setTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditPage, setAuditPage] = useState(1);
  const [auditPages, setAuditPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);

  const isAdmin = hasRole('owner', 'admin');

  const loadUsers = useCallback(async () => {
    try {
      const res = await usersAPI.list();
      setUsers(res.data.users || []);
    } catch (err) {
      console.error('Failed to load users', err);
    }
  }, []);

  const loadRoles = useCallback(async () => {
    try {
      const res = await usersAPI.listRoles();
      setRoles(res.data.roles || []);
    } catch (err) {
      console.error('Failed to load roles', err);
    }
  }, []);

  const loadPermissions = useCallback(async () => {
    try {
      const res = await usersAPI.listPermissions();
      setPermissions(res.data.permissions || []);
    } catch (err) {
      console.error('Failed to load permissions', err);
    }
  }, []);

  const loadAudit = useCallback(async (page = 1) => {
    try {
      const res = await usersAPI.auditLogs({ page, per_page: 30 });
      setAuditLogs(res.data.logs || []);
      setAuditPage(res.data.page);
      setAuditPages(res.data.pages);
    } catch (err) {
      console.error('Failed to load audit logs', err);
    }
  }, []);

  useEffect(() => {
    Promise.all([loadUsers(), loadRoles(), loadPermissions()]).finally(() => setLoading(false));
  }, [loadUsers, loadRoles, loadPermissions]);

  useEffect(() => { if (tab === 'audit') loadAudit(); }, [tab, loadAudit]);

  const handleToggleActive = async (u) => {
    try {
      await usersAPI.activate(u.id, !u.is_active);
      toast.success(`User ${u.is_active ? 'deactivated' : 'activated'}`);
      loadUsers();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed');
    }
  };

  const handleDelete = async (u) => {
    if (!window.confirm(`Delete ${u.full_name}? This cannot be undone.`)) return;
    try {
      await usersAPI.delete(u.id);
      toast.success('User deleted');
      loadUsers();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed');
    }
  };

  const ROLE_COLORS = { owner: 'var(--primary)', admin: '#7C3AED', manager: '#0D9488', user: 'var(--gray-500)', viewer: 'var(--gray-400)' };

  const userColumns = [
    { key: 'full_name', label: 'Name', render: (_, r) => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div className="avatar" style={{ width: 28, height: 28, fontSize: 11 }}>{r.first_name?.[0]}{r.last_name?.[0]}</div>
        <div><div style={{ fontWeight: 500 }}>{r.full_name}</div><div style={{ fontSize: 12, color: 'var(--gray-500)' }}>{r.email}</div></div>
      </div>
    )},
    { key: 'role', label: 'Role', render: (v) => (
      <span className="badge" style={{ background: ROLE_COLORS[v] || 'var(--gray-400)', color: '#fff' }}>{v}</span>
    )},
    { key: 'is_active', label: 'Status', render: (v) => (
      <span className={`badge badge-${v ? 'success' : 'secondary'}`}>{v ? 'Active' : 'Inactive'}</span>
    )},
    { key: 'created_at', label: 'Joined', render: (v) => v ? new Date(v).toLocaleDateString() : '—' },
  ];

  if (isAdmin) {
    userColumns.push({
      key: '_actions', label: '', render: (_, r) => (
        <div style={{ display: 'flex', gap: 4 }}>
          <button className="btn btn-sm btn-secondary" onClick={() => setEditUser(r)}>Edit</button>
          <button className="btn btn-sm btn-secondary" onClick={() => handleToggleActive(r)}>{r.is_active ? 'Disable' : 'Enable'}</button>
          <button className="btn btn-sm btn-danger" onClick={() => handleDelete(r)}>Delete</button>
        </div>
      ),
    });
  }

  const auditColumns = [
    { key: 'created_at', label: 'Time', render: (v) => new Date(v).toLocaleString() },
    { key: 'user_name', label: 'User', render: (v, r) => v || r.user_email || '—' },
    { key: 'action', label: 'Action', render: (v) => <code style={{ fontSize: 12 }}>{v}</code> },
    { key: 'resource_type', label: 'Resource', render: (v, r) => v ? `${v} ${r.resource_id?.slice(0, 8) || ''}` : '—' },
    { key: 'ip_address', label: 'IP' },
  ];

  if (loading) return <div className="loading-spinner" />;

  // Group permissions by module
  const permsByModule = permissions.reduce((acc, p) => {
    if (!acc[p.module]) acc[p.module] = [];
    acc[p.module].push(p);
    return acc;
  }, {});

  return (
    <div>
      <header className="dashboard-header">
        <div>
          <h1>Users & Access</h1>
          <p className="header-subtitle">Manage team members, roles, and permissions</p>
        </div>
        <div className="header-actions">
          {isAdmin && tab === 'users' && (
            <button className="btn btn-primary" onClick={() => setInviteOpen(true)}>
              <UserPlus size={16} /> Invite User
            </button>
          )}
        </div>
      </header>

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: 24 }}>
        <button className={`tab ${tab === 'users' ? 'active' : ''}`} onClick={() => setTab('users')}>
          <UserPlus size={14} /> Users ({users.length})
        </button>
        <button className={`tab ${tab === 'roles' ? 'active' : ''}`} onClick={() => setTab('roles')}>
          <Shield size={14} /> Roles & Permissions
        </button>
        {isAdmin && (
          <button className={`tab ${tab === 'audit' ? 'active' : ''}`} onClick={() => setTab('audit')}>
            <ScrollText size={14} /> Audit Log
          </button>
        )}
      </div>

      {/* Users tab */}
      {tab === 'users' && (
        <div className="card">
          <DataTable columns={userColumns} data={users} emptyMessage="No users found" />
        </div>
      )}

      {/* Roles & Permissions tab */}
      {tab === 'roles' && (
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <h3>Roles</h3>
              {isAdmin && (
                <button className="btn btn-sm btn-secondary" onClick={async () => {
                  await usersAPI.seedRoles();
                  toast.success('Roles seeded');
                  loadRoles();
                }}><RefreshCw size={14} /> Seed Defaults</button>
              )}
            </div>
            <DataTable
              columns={[
                { key: 'name', label: 'Role', render: (v, r) => (
                  <span className="badge" style={{ background: ROLE_COLORS[r.slug] || 'var(--gray-400)', color: '#fff' }}>{v}</span>
                )},
                { key: 'description', label: 'Description' },
                { key: 'level', label: 'Level' },
                { key: 'permissions', label: 'Permissions', render: (v) => (
                  <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>{Array.isArray(v) ? v.length : 0} permissions</span>
                )},
              ]}
              data={roles}
              emptyMessage="No roles"
            />
          </div>

          <div className="card">
            <div className="card-header"><h3>System Permissions</h3></div>
            <div style={{ padding: 16 }}>
              {Object.entries(permsByModule).map(([mod, perms]) => (
                <div key={mod} style={{ marginBottom: 16 }}>
                  <h4 style={{ textTransform: 'capitalize', marginBottom: 8 }}>{mod}</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {perms.map((p) => (
                      <span key={p.slug} className="badge badge-info" style={{ fontSize: 11 }} title={p.description}>{p.slug}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Audit Log tab */}
      {tab === 'audit' && (
        <div className="card">
          <DataTable columns={auditColumns} data={auditLogs} emptyMessage="No audit logs" />
          {auditPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: '12px 0' }}>
              <button className="btn btn-sm btn-secondary" disabled={auditPage <= 1} onClick={() => loadAudit(auditPage - 1)}>Previous</button>
              <span style={{ padding: '4px 8px', fontSize: 13 }}>Page {auditPage} / {auditPages}</span>
              <button className="btn btn-sm btn-secondary" disabled={auditPage >= auditPages} onClick={() => loadAudit(auditPage + 1)}>Next</button>
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      <InviteModal open={inviteOpen} onClose={() => setInviteOpen(false)} onInvited={() => { loadUsers(); toast.success('User invited'); }} roles={roles} />
      <EditModal open={!!editUser} onClose={() => setEditUser(null)} onSaved={() => { loadUsers(); toast.success('User updated'); }} user={editUser} roles={roles} />
    </div>
  );
}
