import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { tenantAPI, subscriptionAPI } from '../services/api';
import analytics from '../services/analytics';
import AppShell from '../components/AppShell';
import OrganisationPage from './OrganisationPage';
import ModuleMarketplace from './ModuleMarketplace';
import InventoryPage from './InventoryPage';
import SalesPage from './SalesPage';
import PurchasingPage from './PurchasingPage';
import UsersPage from './UsersPage';
import ProfilePage from './ProfilePage';
import ActivityPage from './ActivityPage';
import AccountingPage from './AccountingPage';
import CRMPage from './CRMPage';
import HRPage from './HRPage';
import AIInsightsPage from './AIInsightsPage';
import {
  Building2, Users, Package, Clock,
} from 'lucide-react';
import '../styles/dashboard.css';

const PAGE_TABS = [
  'organisation', 'modules', 'inventory', 'sales', 'purchasing',
  'accounting', 'crm', 'hr',
  'ai-insights',
  'users', 'profile', 'activity',
];

function TenantDashboard({ page }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [tenant, setTenant] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(
    PAGE_TABS.includes(page) ? page : 'overview'
  );

  useEffect(() => {
    if (PAGE_TABS.includes(page)) {
      setActiveTab(page);
    } else if (location.pathname === '/dashboard') {
      if (PAGE_TABS.includes(activeTab)) setActiveTab('overview');
    }
  }, [page, location.pathname]);

  useEffect(() => { analytics.pageView('tenant_dashboard'); }, []);

  const loadData = useCallback(async () => {
    if (!user?.tenant_id) return;
    try {
      const [tenantRes, subRes] = await Promise.all([
        tenantAPI.get(user.tenant_id),
        subscriptionAPI.current().catch(() => null),
      ]);
      setTenant(tenantRes.data.tenant);
      if (subRes) setSubscription(subRes.data.subscription);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }, [user?.tenant_id]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  const getStatusColor = (status) => {
    const colors = { trial: 'info', active: 'success', suspended: 'warning', churned: 'danger' };
    return colors[status] || 'info';
  };

  return (
    <AppShell activeKey={activeTab}>
      {activeTab === 'organisation' ? (
        <OrganisationPage />
      ) : activeTab === 'modules' ? (
        <ModuleMarketplace />
      ) : activeTab === 'inventory' ? (
        <InventoryPage />
      ) : activeTab === 'users' ? (
        <UsersPage />
      ) : activeTab === 'profile' ? (
        <ProfilePage />
      ) : activeTab === 'activity' ? (
        <ActivityPage />
      ) : activeTab === 'sales' ? (
        <SalesPage />
      ) : activeTab === 'accounting' ? (
        <AccountingPage />
      ) : activeTab === 'crm' ? (
        <CRMPage />
      ) : activeTab === 'hr' ? (
        <HRPage />
      ) : activeTab === 'ai-insights' ? (
        <AIInsightsPage />
      ) : activeTab === 'profile' ? (
        <ProfilePage />
      ) : (
        <div>
          <header className="dashboard-header">
            <div>
              <h1>Welcome, {user?.first_name}!</h1>
              <p className="header-subtitle">
                {tenant?.name} &middot;{' '}
                <span className={`badge badge-${getStatusColor(tenant?.status)}`}>
                  {tenant?.status}
                </span>
              </p>
            </div>
          </header>

          <div className="dashboard-content">
            {activeTab === 'overview' && (
              <div className="overview-content">
                <div className="stat-grid">
                  <div className="stat-card stat-blue">
                    <div className="stat-card-header">
                      <span className="stat-card-label">Organisation</span>
                      <div className="stat-card-icon"><Building2 size={20} /></div>
                    </div>
                    <div className="stat-card-value">{tenant?.name}</div>
                    <div className="stat-card-trend">{tenant?.slug}</div>
                  </div>
                  <div className="stat-card stat-green">
                    <div className="stat-card-header">
                      <span className="stat-card-label">Current Plan</span>
                      <div className="stat-card-icon"><Package size={20} /></div>
                    </div>
                    <div className="stat-card-value">{subscription?.plan?.name || 'Free'}</div>
                    <div className="stat-card-trend">{subscription?.billing_cycle || 'monthly'} billing</div>
                  </div>
                  <div className="stat-card stat-purple">
                    <div className="stat-card-header">
                      <span className="stat-card-label">Status</span>
                      <div className="stat-card-icon"><Users size={20} /></div>
                    </div>
                    <div className="stat-card-value" style={{ textTransform: 'capitalize' }}>{tenant?.status}</div>
                    <div className="stat-card-trend">Member since {new Date(tenant?.created_at).toLocaleDateString()}</div>
                  </div>
                  {tenant?.status === 'trial' && tenant?.trial_ends_at && (
                    <div className="stat-card stat-orange">
                      <div className="stat-card-header">
                        <span className="stat-card-label">Trial Ends</span>
                        <div className="stat-card-icon"><Clock size={20} /></div>
                      </div>
                      <div className="stat-card-value">
                        {Math.max(0, Math.ceil((new Date(tenant.trial_ends_at) - new Date()) / (1000 * 60 * 60 * 24)))} days
                      </div>
                      <div className="stat-card-trend">{new Date(tenant.trial_ends_at).toLocaleDateString()}</div>
                    </div>
                  )}
                </div>

                <div className="card">
                  <div className="card-header"><h3>Getting Started</h3></div>
                  <div className="card-body">
                    <div className="checklist">
                      <div className="checklist-item completed">
                        <div className="checklist-check">✓</div>
                        <div>
                          <div className="checklist-title">Create your account</div>
                          <div className="checklist-desc">Your organisation is set up and ready to go</div>
                        </div>
                      </div>
                      <div className="checklist-item">
                        <div className="checklist-check">2</div>
                        <div>
                          <div className="checklist-title">
                            <span style={{ cursor: 'pointer', color: 'var(--primary)' }} onClick={() => navigate('/organisation')}>
                              Set up your organisation structure
                            </span>
                          </div>
                          <div className="checklist-desc">Create departments, branches, and teams</div>
                        </div>
                      </div>
                      <div className="checklist-item">
                        <div className="checklist-check">3</div>
                        <div>
                          <div className="checklist-title">
                            <span style={{ cursor: 'pointer', color: 'var(--primary)' }} onClick={() => navigate('/modules')}>
                              Install modules
                            </span>
                          </div>
                          <div className="checklist-desc">Activate Inventory, Sales, and Purchasing modules</div>
                        </div>
                      </div>
                      <div className="checklist-item">
                        <div className="checklist-check">4</div>
                        <div>
                          <div className="checklist-title">Invite your team</div>
                          <div className="checklist-desc">Add users and assign roles (coming in Phase 5)</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'subscription' && (
              <div className="card">
                <div className="card-header"><h3>Subscription Details</h3></div>
                <div className="card-body">
                  {subscription ? (
                    <div className="detail-grid">
                      <div className="detail-item"><div className="detail-label">Plan</div><div className="detail-value">{subscription.plan?.name}</div></div>
                      <div className="detail-item"><div className="detail-label">Price</div><div className="detail-value">${subscription.plan?.price_monthly}/month</div></div>
                      <div className="detail-item"><div className="detail-label">Billing Cycle</div><div className="detail-value">{subscription.billing_cycle}</div></div>
                      <div className="detail-item"><div className="detail-label">Status</div><div className="detail-value"><span className={`badge badge-${subscription.status === 'active' ? 'success' : 'warning'}`}>{subscription.status}</span></div></div>
                      <div className="detail-item"><div className="detail-label">Max Users</div><div className="detail-value">{subscription.plan?.max_users}</div></div>
                      <div className="detail-item"><div className="detail-label">Storage</div><div className="detail-value">{subscription.plan?.max_storage_gb} GB</div></div>
                      <div className="detail-item"><div className="detail-label">Started</div><div className="detail-value">{new Date(subscription.starts_at).toLocaleDateString()}</div></div>
                    </div>
                  ) : (
                    <p className="text-muted">No active subscription. You are on the free plan.</p>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="card">
                <div className="card-header"><h3>Organisation Settings</h3></div>
                <div className="card-body">
                  <div className="detail-grid">
                    <div className="detail-item"><div className="detail-label">Organisation Name</div><div className="detail-value">{tenant?.name}</div></div>
                    <div className="detail-item"><div className="detail-label">Email</div><div className="detail-value">{tenant?.email}</div></div>
                    <div className="detail-item"><div className="detail-label">Phone</div><div className="detail-value">{tenant?.phone || 'Not set'}</div></div>
                    <div className="detail-item"><div className="detail-label">Slug</div><div className="detail-value">{tenant?.slug}</div></div>
                    <div className="detail-item"><div className="detail-label">Timezone</div><div className="detail-value">{tenant?.settings?.timezone || 'UTC'}</div></div>
                    <div className="detail-item"><div className="detail-label">Language</div><div className="detail-value">{tenant?.settings?.language || 'en'}</div></div>
                    <div className="detail-item"><div className="detail-label">Currency</div><div className="detail-value">{tenant?.settings?.currency || 'USD'}</div></div>
                  </div>
                  <p className="text-muted" style={{ marginTop: '1.5rem' }}>Full settings editing will be available in a future update.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}

export default TenantDashboard;
