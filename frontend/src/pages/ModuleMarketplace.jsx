import React, { useState, useEffect, useCallback } from 'react';
import { modulesAPI } from '../services/api';
import analytics from '../services/analytics';
import {
  Package, Download, Trash2, Check, AlertCircle, RefreshCw,
  Box, ShoppingCart, Truck, Search,
} from 'lucide-react';
import '../styles/modules.css';

const ICON_MAP = {
  box: Box,
  'shopping-cart': ShoppingCart,
  truck: Truck,
  package: Package,
};

function ModuleMarketplace() {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const loadModules = useCallback(async () => {
    try {
      setLoading(true);
      // Seed modules first (idempotent)
      await modulesAPI.seed().catch(() => {});
      const res = await modulesAPI.available();
      setModules(res.data.modules || []);
    } catch (err) {
      setError('Failed to load modules');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    analytics.pageView('module_marketplace');
    loadModules();
  }, [loadModules]);

  const handleInstall = async (slug) => {
    setActionLoading(slug);
    setError(null);
    setSuccess(null);
    try {
      const res = await modulesAPI.install(slug);
      setSuccess(`Installed: ${res.data.installed?.join(', ') || slug}`);
      analytics.track('module_installed', { module: slug });
      await loadModules();
    } catch (err) {
      setError(err.response?.data?.error || 'Install failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUninstall = async (slug) => {
    if (!window.confirm(`Uninstall module "${slug}"? This will disable the module for your organisation.`)) return;
    setActionLoading(slug);
    setError(null);
    setSuccess(null);
    try {
      await modulesAPI.uninstall(slug);
      setSuccess(`Module "${slug}" uninstalled`);
      analytics.track('module_uninstalled', { module: slug });
      await loadModules();
    } catch (err) {
      setError(err.response?.data?.error || 'Uninstall failed');
    } finally {
      setActionLoading(null);
    }
  };

  const filtered = modules.filter(m =>
    m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Loading modules...</p>
      </div>
    );
  }

  return (
    <div className="modules-page">
      <header className="page-header">
        <div>
          <h1><Package size={24} /> Module Marketplace</h1>
          <p className="header-subtitle">Install and manage modules for your organisation</p>
        </div>
        <button className="btn btn-secondary" onClick={loadModules}>
          <RefreshCw size={16} /> Refresh
        </button>
      </header>

      {error && (
        <div className="alert alert-danger">
          <AlertCircle size={16} /> {error}
          <button className="alert-close" onClick={() => setError(null)}>&times;</button>
        </div>
      )}
      {success && (
        <div className="alert alert-success">
          <Check size={16} /> {success}
          <button className="alert-close" onClick={() => setSuccess(null)}>&times;</button>
        </div>
      )}

      <div className="search-bar">
        <Search size={18} />
        <input
          type="text"
          placeholder="Search modules..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="modules-grid">
        {filtered.map(mod => {
          const IconComp = ICON_MAP[mod.icon] || Package;
          return (
            <div key={mod.slug} className={`module-card ${mod.is_installed ? 'installed' : ''}`}>
              <div className="module-card-header" style={{ borderTopColor: mod.color || '#6366f1' }}>
                <div className="module-icon" style={{ backgroundColor: mod.color || '#6366f1' }}>
                  <IconComp size={24} color="#fff" />
                </div>
                <div className="module-info">
                  <h3>{mod.name}</h3>
                  <span className="module-version">v{mod.version}</span>
                </div>
                {mod.is_core && <span className="badge badge-info">Core</span>}
              </div>
              <p className="module-description">{mod.description}</p>
              {mod.dependencies?.length > 0 && (
                <div className="module-deps">
                  <small>Requires: {mod.dependencies.join(', ')}</small>
                </div>
              )}
              <div className="module-card-footer">
                <span className={`module-status ${mod.is_installed ? 'active' : ''}`}>
                  {mod.is_installed ? 'Installed' : 'Available'}
                </span>
                {mod.is_installed ? (
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleUninstall(mod.slug)}
                    disabled={actionLoading === mod.slug}
                  >
                    {actionLoading === mod.slug ? <RefreshCw size={14} className="spin" /> : <Trash2 size={14} />}
                    Uninstall
                  </button>
                ) : (
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => handleInstall(mod.slug)}
                    disabled={actionLoading === mod.slug}
                  >
                    {actionLoading === mod.slug ? <RefreshCw size={14} className="spin" /> : <Download size={14} />}
                    Install
                  </button>
                )}
              </div>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <div className="empty-state">
            <Package size={48} />
            <p>No modules found</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ModuleMarketplace;
