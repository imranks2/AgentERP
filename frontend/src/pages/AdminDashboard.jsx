import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { adminAPI, tenantAPI } from '../services/api';
import analytics from '../services/analytics';
import DataTable from '../components/DataTable';
import {
  Zap, LogOut, LayoutDashboard, Users, Building2,
  TrendingUp, Search, ChevronDown, MoreHorizontal,
  ArrowUpRight, ArrowDownRight, Activity, RefreshCw,
  Eye, UserCheck, UserX, XCircle
} from 'lucide-react';
import '../styles/dashboard.css';

function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [tenants, setTenants] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    analytics.pageView('admin_dashboard');
  }, []);

  const loadDashboard = useCallback(async () => {
    try {
      const response = await adminAPI.dashboard();
      setDashboardData(response.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    }
  }, []);

  const loadTenants = useCallback(async () => {
    try {
      const response = await adminAPI.listTenants({
        page: currentPage,
        per_page: 10,
        status: statusFilter || undefined,
        search: searchQuery || undefined,
      });
      setTenants(response.data);
    } catch (err) {
      console.error('Failed to load tenants:', err);
    }
  }, [currentPage, statusFilter, searchQuery]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([loadDashboard(), loadTenants()]);
      setLoading(false);
    };
    load();
  }, [loadDashboard, loadTenants]);

  const handleStatusChange = async (tenantId, newStatus) => {
    try {
      await tenantAPI.changeStatus(tenantId, newStatus);
      await Promise.all([loadDashboard(), loadTenants()]);
      analytics.featureUsed('admin_change_tenant_status', { tenantId, newStatus });
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to update status');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const statCards = dashboardData ? [
    {
      label: 'Total Tenants',
      value: dashboardData.tenants?.total || 0,
      icon: <Building2 size={20} />,
      trend: '+12%',
      trendUp: true,
      color: 'blue',
    },
    {
      label: 'Active Tenants',
      value: (dashboardData.tenants?.active || 0) + (dashboardData.tenants?.trial || 0),
      icon: <UserCheck size={20} />,
      trend: '+8%',
      trendUp: true,
      color: 'green',
    },
    {
      label: 'Total Users',
      value: dashboardData.users?.total || 0,
      icon: <Users size={20} />,
      trend: '+15%',
      trendUp: true,
      color: 'purple',
    },
    {
      label: 'Events (30d)',
      value: dashboardData.analytics?.total_events || 0,
      icon: <Activity size={20} />,
      trend: '+23%',
      trendUp: true,
      color: 'orange',
    },
  ] : [];

  const getStatusBadge = (status) => {
    const classes = {
      trial: 'badge badge-info',
      active: 'badge badge-success',
      suspended: 'badge badge-warning',
      churned: 'badge badge-danger',
    };
    return <span className={classes[status] || 'badge'}>{status}</span>;
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Loading admin dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="nav-logo">
            <Zap size={20} />
            <span>AgentERP</span>
          </div>
          <span className="sidebar-badge">Admin</span>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`sidebar-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <LayoutDashboard size={18} />
            Overview
          </button>
          <button
            className={`sidebar-item ${activeTab === 'tenants' ? 'active' : ''}`}
            onClick={() => setActiveTab('tenants')}
          >
            <Building2 size={18} />
            Tenants
          </button>
          <button
            className={`sidebar-item ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <TrendingUp size={18} />
            Analytics
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">{user?.first_name?.[0]}{user?.last_name?.[0]}</div>
            <div className="user-info">
              <div className="user-name">{user?.full_name}</div>
              <div className="user-role">Platform Admin</div>
            </div>
          </div>
          <button className="sidebar-logout" onClick={handleLogout}>
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <h1>
              {activeTab === 'overview' && 'Dashboard Overview'}
              {activeTab === 'tenants' && 'Tenant Management'}
              {activeTab === 'analytics' && 'Platform Analytics'}
            </h1>
            <p className="header-subtitle">
              {activeTab === 'overview' && 'Platform-wide metrics and health'}
              {activeTab === 'tenants' && 'Manage all registered organisations'}
              {activeTab === 'analytics' && 'AI training data and interaction insights'}
            </p>
          </div>
          <button className="btn-icon" onClick={() => { loadDashboard(); loadTenants(); }}>
            <RefreshCw size={18} />
          </button>
        </header>

        <div className="dashboard-content">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <>
              <div className="stat-grid">
                {statCards.map((stat, i) => (
                  <div key={i} className={`stat-card stat-${stat.color}`}>
                    <div className="stat-card-header">
                      <span className="stat-card-label">{stat.label}</span>
                      <div className="stat-card-icon">{stat.icon}</div>
                    </div>
                    <div className="stat-card-value">{stat.value.toLocaleString()}</div>
                    <div className={`stat-card-trend ${stat.trendUp ? 'up' : 'down'}`}>
                      {stat.trendUp ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      {stat.trend} from last month
                    </div>
                  </div>
                ))}
              </div>

              <div className="card-grid">
                <div className="card">
                  <div className="card-header">
                    <h3>Tenant Distribution</h3>
                  </div>
                  <div className="card-body">
                    {dashboardData?.tenants && (
                      <div className="distribution-chart">
                        {Object.entries(dashboardData.tenants.by_status || {}).map(([status, count]) => (
                          <div key={status} className="distribution-item">
                            <div className="distribution-label">
                              {getStatusBadge(status)}
                              <span className="distribution-count">{count}</span>
                            </div>
                            <div className="distribution-bar">
                              <div
                                className={`distribution-fill status-${status}`}
                                style={{
                                  width: `${dashboardData.tenants.total > 0 ? (count / dashboardData.tenants.total) * 100 : 0}%`
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="card">
                  <div className="card-header">
                    <h3>Subscription Overview</h3>
                  </div>
                  <div className="card-body">
                    {dashboardData?.subscriptions && (
                      <div className="distribution-chart">
                        {Object.entries(dashboardData.subscriptions.by_plan || {}).map(([plan, count]) => (
                          <div key={plan} className="distribution-item">
                            <div className="distribution-label">
                              <span className="badge">{plan}</span>
                              <span className="distribution-count">{count}</span>
                            </div>
                            <div className="distribution-bar">
                              <div
                                className="distribution-fill plan-fill"
                                style={{
                                  width: `${dashboardData.subscriptions.total > 0 ? (count / dashboardData.subscriptions.total) * 100 : 0}%`
                                }}
                              />
                            </div>
                          </div>
                        ))}
                        {Object.keys(dashboardData.subscriptions.by_plan || {}).length === 0 && (
                          <p className="text-muted">No subscriptions yet</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Tenants Tab */}
          {activeTab === 'tenants' && (
            <>
              <div className="toolbar">
                <div className="search-box">
                  <Search size={18} />
                  <input
                    type="text"
                    placeholder="Search tenants..."
                    value={searchQuery}
                    onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                  />
                </div>
                <div className="filter-group">
                  <select
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
                    className="filter-select"
                  >
                    <option value="">All Statuses</option>
                    <option value="trial">Trial</option>
                    <option value="active">Active</option>
                    <option value="suspended">Suspended</option>
                    <option value="churned">Churned</option>
                  </select>
                </div>
              </div>

              <div className="card">
                <DataTable
                  columns={[
                    { key: 'name', label: 'Organisation', sortable: true, primary: true, render: (_, t) => (
                      <><div className="cell-primary">{t.name}</div><div className="cell-secondary">{t.slug}</div></>
                    )},
                    { key: 'email', label: 'Email', sortable: true },
                    { key: 'status', label: 'Status', render: (v) => getStatusBadge(v) },
                    { key: '_plan', label: 'Plan', render: (_, t) => t.subscription?.plan?.name || 'None' },
                    { key: 'user_count', label: 'Users', render: (v) => v || 0 },
                    { key: 'created_at', label: 'Created', sortable: true, render: (v) => new Date(v).toLocaleDateString() },
                    { key: '_actions', label: 'Actions', render: (_, tenant) => (
                      <div className="action-group">
                        {tenant.status === 'trial' && (
                          <button className="btn-sm btn-success" onClick={(e) => { e.stopPropagation(); handleStatusChange(tenant.id, 'active'); }} title="Activate"><UserCheck size={14} /></button>
                        )}
                        {tenant.status === 'active' && (
                          <button className="btn-sm btn-warning" onClick={(e) => { e.stopPropagation(); handleStatusChange(tenant.id, 'suspended'); }} title="Suspend"><UserX size={14} /></button>
                        )}
                        {tenant.status === 'suspended' && (
                          <button className="btn-sm btn-success" onClick={(e) => { e.stopPropagation(); handleStatusChange(tenant.id, 'active'); }} title="Reactivate"><UserCheck size={14} /></button>
                        )}
                        {tenant.status !== 'churned' && (
                          <button className="btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); handleStatusChange(tenant.id, 'churned'); }} title="Churn"><XCircle size={14} /></button>
                        )}
                      </div>
                    )},
                  ]}
                  data={tenants?.items || []}
                  searchable={false}
                  paginate={false}
                  emptyTitle="No tenants found"
                  emptyDesc="No tenants match your current filters"
                />

                {tenants?.pages > 1 && (
                  <div className="pagination">
                    <button
                      disabled={currentPage <= 1}
                      onClick={() => setCurrentPage(p => p - 1)}
                    >
                      Previous
                    </button>
                    <span>Page {currentPage} of {tenants.pages}</span>
                    <button
                      disabled={currentPage >= tenants.pages}
                      onClick={() => setCurrentPage(p => p + 1)}
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="card">
              <div className="card-header">
                <h3>Analytics Overview (Last 30 Days)</h3>
              </div>
              <div className="card-body">
                <div className="analytics-summary">
                  <div className="analytics-stat">
                    <div className="analytics-stat-value">
                      {dashboardData?.analytics?.total_events?.toLocaleString() || 0}
                    </div>
                    <div className="analytics-stat-label">Total Events</div>
                  </div>
                  {dashboardData?.analytics?.by_type && Object.entries(dashboardData.analytics.by_type).map(([type, count]) => (
                    <div key={type} className="analytics-stat">
                      <div className="analytics-stat-value">{count.toLocaleString()}</div>
                      <div className="analytics-stat-label">{type.replace('_', ' ')}</div>
                    </div>
                  ))}
                </div>
                <p className="text-muted" style={{ marginTop: '2rem' }}>
                  Detailed analytics with charts and drill-down capabilities will be available in Phase 4.
                  All interaction data is being captured for AI training.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default AdminDashboard;
