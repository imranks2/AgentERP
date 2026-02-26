import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';
import { usersAPI } from '../services/api';
import { useToast } from '../components/Toast';
import { User, Lock, Shield } from 'lucide-react';

export default function ProfilePage() {
  const { user, loadUser } = useAuth();
  const toast = useToast();
  const [tab, setTab] = useState('profile');
  const [profileForm, setProfileForm] = useState({ first_name: user?.first_name || '', last_name: user?.last_name || '' });
  const [pwForm, setPwForm] = useState({ current_password: '', password: '', confirm: '' });
  const [saving, setSaving] = useState(false);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await usersAPI.updateProfile(profileForm);
      await loadUser();
      toast.success('Profile updated');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed');
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordSave = async (e) => {
    e.preventDefault();
    if (pwForm.password !== pwForm.confirm) { toast.error('Passwords do not match'); return; }
    if (pwForm.password.length < 6) { toast.error('Password must be at least 6 characters'); return; }
    setSaving(true);
    try {
      await usersAPI.updateProfile({ current_password: pwForm.current_password, password: pwForm.password });
      toast.success('Password changed');
      setPwForm({ current_password: '', password: '', confirm: '' });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <header className="dashboard-header">
        <div>
          <h1>My Profile</h1>
          <p className="header-subtitle">{user?.email}</p>
        </div>
      </header>

      <div className="tabs" style={{ marginBottom: 24 }}>
        <button className={`tab ${tab === 'profile' ? 'active' : ''}`} onClick={() => setTab('profile')}>
          <User size={14} /> Profile
        </button>
        <button className={`tab ${tab === 'security' ? 'active' : ''}`} onClick={() => setTab('security')}>
          <Lock size={14} /> Security
        </button>
        <button className={`tab ${tab === 'permissions' ? 'active' : ''}`} onClick={() => setTab('permissions')}>
          <Shield size={14} /> My Permissions
        </button>
      </div>

      {tab === 'profile' && (
        <div className="card" style={{ maxWidth: 480, padding: 24 }}>
          <form onSubmit={handleProfileSave}>
            <div className="form-group">
              <label>First Name</label>
              <input value={profileForm.first_name} onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Last Name</label>
              <input value={profileForm.last_name} onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input disabled value={user?.email || ''} />
            </div>
            <div className="form-group">
              <label>Role</label>
              <input disabled value={user?.role || ''} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save Changes'}</button>
          </form>
        </div>
      )}

      {tab === 'security' && (
        <div className="card" style={{ maxWidth: 480, padding: 24 }}>
          <h3 style={{ marginBottom: 16 }}>Change Password</h3>
          <form onSubmit={handlePasswordSave}>
            <div className="form-group">
              <label>Current Password</label>
              <input type="password" required value={pwForm.current_password} onChange={(e) => setPwForm({ ...pwForm, current_password: e.target.value })} />
            </div>
            <div className="form-group">
              <label>New Password</label>
              <input type="password" required value={pwForm.password} onChange={(e) => setPwForm({ ...pwForm, password: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Confirm Password</label>
              <input type="password" required value={pwForm.confirm} onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Change Password'}</button>
          </form>
        </div>
      )}

      {tab === 'permissions' && (
        <div className="card" style={{ padding: 24 }}>
          <h3 style={{ marginBottom: 8 }}>Your Permissions</h3>
          <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 16 }}>
            Role: <strong>{user?.role}</strong> — {user?.role_name || user?.role}
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {(user?.permissions || []).length === 0 ?
              <span style={{ color: 'var(--gray-400)' }}>No specific permissions (may inherit from role)</span> :
              (user?.permissions || []).map((p) => (
                <span key={p} className="badge badge-info" style={{ fontSize: 11 }}>{p}</span>
              ))
            }
          </div>
        </div>
      )}
    </div>
  );
}
