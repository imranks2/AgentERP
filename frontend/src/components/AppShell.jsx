import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import CommandPalette from '../components/CommandPalette';
import Breadcrumbs from '../components/Breadcrumbs';
import {
  Zap, LogOut, LayoutDashboard, Settings, CreditCard,
  Network, Box, ShoppingCart, Truck, Puzzle, Users, User,
  Activity, Bot, BookOpen, Target, UserCheck, Brain, Lightbulb,
  PanelLeftClose, PanelLeft,
} from 'lucide-react';
import NotificationBell from '../components/NotificationBell';
import AIChatPanel from '../components/AIChatPanel';
import AISuggestionsSidebar from '../components/AISuggestionsSidebar';
import '../styles/ai.css';

const ICON_MAP = {
  LayoutDashboard, Network, Puzzle, Box, ShoppingCart, Truck, CreditCard, Settings, Users, User, Activity, Bot,
  BookOpen, Target, UserCheck, Brain,
};

const NAV = [
  { key: 'overview',     label: 'Dashboard',    icon: 'LayoutDashboard', path: '/dashboard' },
  { key: 'organisation', label: 'Organisation', icon: 'Network',         path: '/organisation' },
  { key: 'modules',      label: 'Modules',      icon: 'Puzzle',          path: '/modules' },
  { type: 'divider' },
  { type: 'label', text: 'ERP Modules' },
  { key: 'inventory',    label: 'Inventory',    icon: 'Box',             path: '/inventory' },
  { key: 'sales',        label: 'Sales',        icon: 'ShoppingCart',    path: '/sales' },
  { key: 'purchasing',   label: 'Purchasing',   icon: 'Truck',           path: '/purchasing' },
  { key: 'accounting',   label: 'Accounting',   icon: 'BookOpen',        path: '/accounting' },
  { key: 'crm',          label: 'CRM',          icon: 'Target',          path: '/crm' },
  { key: 'hr',           label: 'HR',           icon: 'UserCheck',       path: '/hr' },
  { type: 'divider' },
  { type: 'label', text: 'Intelligence' },
  { key: 'ai-insights',  label: 'AI Insights',  icon: 'Brain',           path: '/ai-insights' },
  { type: 'divider' },
  { type: 'label', text: 'Administration' },
  { key: 'users',        label: 'Users & Access', icon: 'Users',         path: '/users' },
  { key: 'activity',     label: 'Activity',       icon: 'Activity',      path: '/activity' },
  { key: 'subscription', label: 'Subscription', icon: 'CreditCard',     path: '/dashboard' },
  { key: 'settings',     label: 'Settings',     icon: 'Settings',       path: '/dashboard' },
  { type: 'divider' },
  { key: 'profile',      label: 'My Profile',   icon: 'User',           path: '/profile' },
];

/**
 * Breadcrumb trail derived from current pathname.
 */
function pathToCrumbs(pathname) {
  const map = {};
  NAV.forEach((n) => { if (n.key) map[n.path] = n.label; });

  const crumbs = [{ label: 'Home', path: '/dashboard' }];
  const matched = map[pathname];
  if (matched && pathname !== '/dashboard') {
    crumbs.push({ label: matched, path: pathname });
  }
  return crumbs;
}

/**
 * AppShell — Main layout with collapsible sidebar, command palette, and breadcrumbs.
 *
 * @param {Object}          props
 * @param {string}          props.activeKey  - Current nav key
 * @param {React.ReactNode} props.children   - Page content
 */
export default function AppShell({ activeKey, children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);

  // ⌘K / Ctrl+K listener
  const handleGlobalKey = useCallback((e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      setCmdOpen((v) => !v);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleGlobalKey);
    return () => window.removeEventListener('keydown', handleGlobalKey);
  }, [handleGlobalKey]);

  const handleLogout = () => { logout(); navigate('/'); };

  const crumbs = pathToCrumbs(location.pathname);

  return (
    <div className="dashboard-layout">
      {/* ── Sidebar ────────────────────────────────── */}
      <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="nav-logo">
            <Zap size={20} />
            {!collapsed && <span>AgentERP</span>}
          </div>
          <button
            className="sidebar-toggle"
            onClick={() => setCollapsed((c) => !c)}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV.map((item, i) => {
            if (item.type === 'divider') return <div key={`d${i}`} className="sidebar-divider" />;
            if (item.type === 'label')   return !collapsed ? <div key={`l${i}`} className="sidebar-section-label">{item.text}</div> : null;

            const Icon = ICON_MAP[item.icon];
            return (
              <button
                key={item.key}
                className={`sidebar-item ${activeKey === item.key ? 'active' : ''}`}
                onClick={() => navigate(item.path)}
                title={collapsed ? item.label : undefined}
              >
                {Icon && <Icon size={18} />}
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          {!collapsed && (
            <div className="sidebar-user">
              <div className="avatar">{user?.first_name?.[0]}{user?.last_name?.[0]}</div>
              <div className="user-info">
                <div className="user-name">{user?.full_name}</div>
                <div className="user-role">{user?.role}</div>
              </div>
            </div>
          )}
          {collapsed && (
            <div className="sidebar-user">
              <div className="avatar">{user?.first_name?.[0]}{user?.last_name?.[0]}</div>
            </div>
          )}
          <button className="sidebar-logout" onClick={handleLogout} title="Sign out">
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      {/* ── Main content ──────────────────────────── */}
      <main className={`dashboard-main ${collapsed ? 'sidebar-is-collapsed' : ''}`}>
        {/* Top bar with breadcrumbs and ⌘K hint */}
        <div className="topbar">
          <Breadcrumbs items={crumbs} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              className="topbar-cmd-btn"
              onClick={() => setSuggestionsOpen((v) => !v)}
              title="AI Suggestions"
              style={{ padding: '6px 10px', minWidth: 'auto' }}
            >
              <Lightbulb size={16} />
              <span>Suggestions</span>
            </button>
            <NotificationBell />
            <button className="topbar-cmd-btn" onClick={() => setCmdOpen(true)}>
              <span>Search or jump to…</span>
              <kbd className="cmd-kbd">⌘K</kbd>
            </button>
          </div>
        </div>

        {children}
      </main>

      {/* ── Command Palette ───────────────────────── */}
      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />

      {/* ── AI Chat Panel ─────────────────────────── */}
      <AIChatPanel open={aiOpen} onClose={() => setAiOpen(false)} />
      {!aiOpen && (
        <button className="ai-fab" onClick={() => setAiOpen(true)} title="AI Assistant">
          <Bot size={22} />
        </button>
      )}

      {/* ── AI Suggestions Sidebar ────────────────── */}
      <AISuggestionsSidebar
        isOpen={suggestionsOpen}
        onClose={() => setSuggestionsOpen(false)}
      />
    </div>
  );
}
