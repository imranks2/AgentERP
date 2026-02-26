import React, { useState, useEffect, useCallback, useRef } from 'react';
import { organisationAPI } from '../services/api';
import analytics from '../services/analytics';
import {
  ChevronRight, ChevronDown, Plus, Edit2, Trash2, Move,
  Building2, Briefcase, GitBranch, Users, FolderKanban,
  Search, X, MoreVertical, GripVertical, MapPin,
  Mail, Phone, User, Info, Network,
} from 'lucide-react';
import '../styles/organisation.css';

/* ── unit‑type icon map ─────────────────────────────────────── */
const UNIT_TYPE_ICONS = {
  enterprise:    Building2,
  legal_entity:  Briefcase,
  business_unit: FolderKanban,
  branch:        GitBranch,
  department:    Users,
  project:       FolderKanban,
  cost_center:   Briefcase,
  team:          Users,
};

const UNIT_TYPE_LABELS = {
  enterprise:    'Enterprise',
  legal_entity:  'Legal Entity',
  business_unit: 'Business Unit',
  branch:        'Branch',
  department:    'Department',
  project:       'Project',
  cost_center:   'Cost Center',
  team:          'Team',
};

const UNIT_TYPE_COLORS = {
  enterprise:    '#6366f1',
  legal_entity:  '#8b5cf6',
  business_unit: '#3b82f6',
  branch:        '#06b6d4',
  department:    '#10b981',
  project:       '#f59e0b',
  cost_center:   '#ef4444',
  team:          '#ec4899',
};

/* ── Tree node component ────────────────────────────────────── */
function TreeNode({
  node, level = 0, selectedId, onSelect, onToggle, expandedIds,
  onDragStart, onDragOver, onDrop, dragOverId,
}) {
  const isExpanded = expandedIds.has(node.id);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedId === node.id;
  const isDragOver = dragOverId === node.id;
  const Icon = UNIT_TYPE_ICONS[node.unit_type] || Building2;

  return (
    <div className="tree-node-wrapper">
      <div
        className={`tree-node ${isSelected ? 'selected' : ''} ${isDragOver ? 'drag-over' : ''}`}
        style={{ paddingLeft: `${level * 24 + 8}px` }}
        onClick={() => onSelect(node)}
        draggable
        onDragStart={(e) => onDragStart(e, node)}
        onDragOver={(e) => onDragOver(e, node)}
        onDrop={(e) => onDrop(e, node)}
      >
        <span className="tree-node-grip" title="Drag to move">
          <GripVertical size={14} />
        </span>
        <button
          className="tree-toggle"
          onClick={(e) => { e.stopPropagation(); onToggle(node.id); }}
          style={{ visibility: hasChildren ? 'visible' : 'hidden' }}
        >
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
        <span
          className="tree-node-icon"
          style={{ color: UNIT_TYPE_COLORS[node.unit_type] }}
        >
          <Icon size={16} />
        </span>
        <span className="tree-node-name">{node.name}</span>
        {node.code && <span className="tree-node-code">{node.code}</span>}
        <span className="tree-node-type-badge" style={{
          backgroundColor: `${UNIT_TYPE_COLORS[node.unit_type]}15`,
          color: UNIT_TYPE_COLORS[node.unit_type],
        }}>
          {UNIT_TYPE_LABELS[node.unit_type]}
        </span>
      </div>
      {isExpanded && hasChildren && (
        <div className="tree-children">
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              onToggle={onToggle}
              expandedIds={expandedIds}
              onDragStart={onDragStart}
              onDragOver={onDragOver}
              onDrop={onDrop}
              dragOverId={dragOverId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Breadcrumb component ───────────────────────────────────── */
function Breadcrumbs({ ancestors, current, onNavigate }) {
  return (
    <div className="org-breadcrumbs">
      <button className="breadcrumb-item" onClick={() => onNavigate(null)}>
        <Network size={14} /> Organisation
      </button>
      {ancestors && ancestors.map((a) => (
        <React.Fragment key={a.id}>
          <ChevronRight size={14} className="breadcrumb-sep" />
          <button className="breadcrumb-item" onClick={() => onNavigate(a.id)}>
            {a.name}
          </button>
        </React.Fragment>
      ))}
      {current && (
        <>
          <ChevronRight size={14} className="breadcrumb-sep" />
          <span className="breadcrumb-current">{current.name}</span>
        </>
      )}
    </div>
  );
}

/* ── Unit form modal ────────────────────────────────────────── */
function UnitFormModal({ unit, parentId, onSave, onClose }) {
  const [form, setForm] = useState({
    name: unit?.name || '',
    code: unit?.code || '',
    unit_type: unit?.unit_type || 'department',
    description: unit?.description || '',
    manager_name: unit?.manager_name || '',
    email: unit?.email || '',
    phone: unit?.phone || '',
    address: unit?.address || '',
    is_active: unit?.is_active ?? true,
    parent_id: unit?.parent_id || parentId || null,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const isEditing = !!unit;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setError('Name is required'); return; }
    setSaving(true);
    setError('');
    try {
      await onSave(form, unit?.id);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content org-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{isEditing ? 'Edit Unit' : 'Create Unit'}</h3>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        <form onSubmit={handleSubmit} className="org-form">
          {error && <div className="form-error">{error}</div>}

          <div className="form-row">
            <div className="form-group">
              <label>Name <span className="required">*</span></label>
              <input
                type="text" value={form.name} autoFocus
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g. Finance Department"
              />
            </div>
            <div className="form-group">
              <label>Code</label>
              <input
                type="text" value={form.code}
                onChange={(e) => handleChange('code', e.target.value)}
                placeholder="e.g. DEPT-FIN"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Type <span className="required">*</span></label>
              <select
                value={form.unit_type}
                onChange={(e) => handleChange('unit_type', e.target.value)}
              >
                {Object.entries(UNIT_TYPE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Status</label>
              <select
                value={form.is_active ? 'active' : 'inactive'}
                onChange={(e) => handleChange('is_active', e.target.value === 'active')}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={form.description} rows={2}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Brief description of this unit..."
            />
          </div>

          <div className="form-section-title">Contact Information</div>

          <div className="form-row">
            <div className="form-group">
              <label><User size={14} /> Manager</label>
              <input
                type="text" value={form.manager_name}
                onChange={(e) => handleChange('manager_name', e.target.value)}
                placeholder="Manager name"
              />
            </div>
            <div className="form-group">
              <label><Mail size={14} /> Email</label>
              <input
                type="email" value={form.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="unit@example.com"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label><Phone size={14} /> Phone</label>
              <input
                type="text" value={form.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                placeholder="+1 (555) 123-4567"
              />
            </div>
            <div className="form-group">
              <label><MapPin size={14} /> Address</label>
              <input
                type="text" value={form.address}
                onChange={(e) => handleChange('address', e.target.value)}
                placeholder="123 Main St"
              />
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : isEditing ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Detail panel ───────────────────────────────────────────── */
function DetailPanel({ unit, ancestors, onEdit, onDelete, onAddChild, onClose }) {
  const Icon = UNIT_TYPE_ICONS[unit.unit_type] || Building2;

  return (
    <div className="detail-panel">
      <div className="detail-panel-header">
        <div className="detail-panel-title">
          <span
            className="detail-icon"
            style={{ backgroundColor: `${UNIT_TYPE_COLORS[unit.unit_type]}15`, color: UNIT_TYPE_COLORS[unit.unit_type] }}
          >
            <Icon size={20} />
          </span>
          <div>
            <h3>{unit.name}</h3>
            {unit.code && <span className="detail-code">{unit.code}</span>}
          </div>
        </div>
        <button className="modal-close" onClick={onClose}><X size={18} /></button>
      </div>

      <Breadcrumbs ancestors={ancestors} current={unit} onNavigate={() => {}} />

      <div className="detail-panel-body">
        <div className="detail-section">
          <div className="detail-row">
            <span className="detail-label">Type</span>
            <span className="detail-value">
              <span className="tree-node-type-badge" style={{
                backgroundColor: `${UNIT_TYPE_COLORS[unit.unit_type]}15`,
                color: UNIT_TYPE_COLORS[unit.unit_type],
              }}>
                {UNIT_TYPE_LABELS[unit.unit_type]}
              </span>
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Status</span>
            <span className="detail-value">
              <span className={`badge badge-${unit.is_active ? 'success' : 'warning'}`}>
                {unit.is_active ? 'Active' : 'Inactive'}
              </span>
            </span>
          </div>
          {unit.description && (
            <div className="detail-row">
              <span className="detail-label">Description</span>
              <span className="detail-value">{unit.description}</span>
            </div>
          )}
          <div className="detail-row">
            <span className="detail-label">Depth</span>
            <span className="detail-value">Level {unit.depth}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Created</span>
            <span className="detail-value">{new Date(unit.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        {(unit.manager_name || unit.email || unit.phone || unit.address) && (
          <div className="detail-section">
            <h4 className="detail-section-title"><Info size={14} /> Contact</h4>
            {unit.manager_name && (
              <div className="detail-row">
                <span className="detail-label"><User size={14} /> Manager</span>
                <span className="detail-value">{unit.manager_name}</span>
              </div>
            )}
            {unit.email && (
              <div className="detail-row">
                <span className="detail-label"><Mail size={14} /> Email</span>
                <span className="detail-value">{unit.email}</span>
              </div>
            )}
            {unit.phone && (
              <div className="detail-row">
                <span className="detail-label"><Phone size={14} /> Phone</span>
                <span className="detail-value">{unit.phone}</span>
              </div>
            )}
            {unit.address && (
              <div className="detail-row">
                <span className="detail-label"><MapPin size={14} /> Address</span>
                <span className="detail-value">{unit.address}</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="detail-panel-actions">
        <button className="btn btn-sm btn-primary" onClick={onAddChild}>
          <Plus size={14} /> Add Child
        </button>
        <button className="btn btn-sm btn-ghost" onClick={onEdit}>
          <Edit2 size={14} /> Edit
        </button>
        <button className="btn btn-sm btn-danger" onClick={onDelete}>
          <Trash2 size={14} /> Delete
        </button>
      </div>
    </div>
  );
}

/* ── Main page component ────────────────────────────────────── */
function OrganisationPage() {
  const [tree, setTree] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [ancestors, setAncestors] = useState([]);
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingUnit, setEditingUnit] = useState(null);
  const [parentIdForCreate, setParentIdForCreate] = useState(null);
  const [dragOverId, setDragOverId] = useState(null);
  const dragNodeRef = useRef(null);
  const [notification, setNotification] = useState(null);

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3000);
  };

  /* ── data loading ──────────────────────────── */

  const loadTree = useCallback(async () => {
    try {
      const [treeRes, statsRes] = await Promise.all([
        organisationAPI.tree(),
        organisationAPI.stats(),
      ]);
      setTree(treeRes.data.tree);
      setStats(statsRes.data.stats);
    } catch (err) {
      setError('Failed to load organisation data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    analytics.pageView('organisation');
    loadTree();
  }, [loadTree]);

  /* ── search ────────────────────────────────── */

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await organisationAPI.list({
          search: searchQuery, include_inactive: 'true',
        });
        setSearchResults(res.data.units);
      } catch (err) {
        console.error('Search failed:', err);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  /* ── select unit ───────────────────────────── */

  const handleSelect = useCallback(async (node) => {
    setSelectedUnit(node);
    analytics.track('org_unit_selected', { unit_type: node.unit_type, depth: node.depth });
    try {
      const res = await organisationAPI.ancestors(node.id);
      setAncestors(res.data.ancestors);
    } catch {
      setAncestors([]);
    }
  }, []);

  /* ── expand / collapse ─────────────────────── */

  const handleToggle = useCallback((id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const expandAll = () => {
    const ids = new Set();
    const walk = (nodes) => nodes.forEach((n) => {
      if (n.children?.length) { ids.add(n.id); walk(n.children); }
    });
    walk(tree);
    setExpandedIds(ids);
  };

  const collapseAll = () => setExpandedIds(new Set());

  /* ── drag & drop (move) ────────────────────── */

  const handleDragStart = (e, node) => {
    dragNodeRef.current = node;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', node.id);
  };

  const handleDragOver = (e, node) => {
    e.preventDefault();
    if (dragNodeRef.current && dragNodeRef.current.id !== node.id) {
      setDragOverId(node.id);
    }
  };

  const handleDrop = async (e, targetNode) => {
    e.preventDefault();
    setDragOverId(null);
    const dragNode = dragNodeRef.current;
    dragNodeRef.current = null;
    if (!dragNode || dragNode.id === targetNode.id) return;

    try {
      await organisationAPI.move(dragNode.id, targetNode.id);
      showNotification(`Moved "${dragNode.name}" under "${targetNode.name}"`);
      analytics.track('org_unit_moved', {
        unit_id: dragNode.id, new_parent_id: targetNode.id,
      });
      await loadTree();
      // keep target expanded
      setExpandedIds((prev) => new Set([...prev, targetNode.id]));
    } catch (err) {
      showNotification(err.response?.data?.error || 'Move failed', 'error');
    }
  };

  /* ── CRUD callbacks ────────────────────────── */

  const handleCreateRoot = () => {
    setEditingUnit(null);
    setParentIdForCreate(null);
    setShowModal(true);
  };

  const handleAddChild = () => {
    if (!selectedUnit) return;
    setEditingUnit(null);
    setParentIdForCreate(selectedUnit.id);
    setShowModal(true);
  };

  const handleEdit = () => {
    if (!selectedUnit) return;
    setEditingUnit(selectedUnit);
    setParentIdForCreate(null);
    setShowModal(true);
  };

  const handleSave = async (formData, unitId) => {
    if (unitId) {
      await organisationAPI.update(unitId, formData);
      showNotification('Unit updated');
      analytics.track('org_unit_updated', { unit_id: unitId });
    } else {
      await organisationAPI.create(formData);
      showNotification('Unit created');
      analytics.track('org_unit_created', { unit_type: formData.unit_type });
    }
    setShowModal(false);
    setEditingUnit(null);
    await loadTree();
  };

  const handleDelete = async () => {
    if (!selectedUnit) return;
    const confirmMsg = selectedUnit.children?.length
      ? `Delete "${selectedUnit.name}" and all its children?`
      : `Delete "${selectedUnit.name}"?`;
    if (!window.confirm(confirmMsg)) return;

    try {
      await organisationAPI.delete(selectedUnit.id);
      showNotification('Unit deleted');
      analytics.track('org_unit_deleted', { unit_id: selectedUnit.id });
      setSelectedUnit(null);
      setAncestors([]);
      await loadTree();
    } catch (err) {
      showNotification(err.response?.data?.error || 'Delete failed', 'error');
    }
  };

  /* ── render ────────────────────────────────── */

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Loading organisation...</p>
      </div>
    );
  }

  const displayNodes = searchResults || tree;

  return (
    <div className="org-page">
      {/* Notification toast */}
      {notification && (
        <div className={`org-toast ${notification.type}`}>{notification.msg}</div>
      )}

      {/* Toolbar */}
      <div className="org-toolbar">
        <div className="org-toolbar-left">
          <h2><Network size={22} /> Organisation</h2>
          {stats && (
            <span className="org-stats-badge">
              {stats.active_units} unit{stats.active_units !== 1 ? 's' : ''}
              {stats.max_depth > 0 && ` · ${stats.max_depth + 1} levels`}
            </span>
          )}
        </div>
        <div className="org-toolbar-right">
          <div className="org-search-box">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search units..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="search-clear" onClick={() => setSearchQuery('')}>
                <X size={14} />
              </button>
            )}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={expandAll} title="Expand all">
            <ChevronDown size={16} /> Expand
          </button>
          <button className="btn btn-ghost btn-sm" onClick={collapseAll} title="Collapse all">
            <ChevronRight size={16} /> Collapse
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleCreateRoot}>
            <Plus size={16} /> Add Root Unit
          </button>
        </div>
      </div>

      <div className="org-content">
        {/* Tree panel */}
        <div className={`org-tree-panel ${selectedUnit ? 'has-detail' : ''}`}>
          {error && <div className="org-error">{error}</div>}

          {searchResults !== null && (
            <div className="search-results-header">
              <span>{searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"</span>
              <button className="btn btn-ghost btn-sm" onClick={() => setSearchQuery('')}>
                Clear
              </button>
            </div>
          )}

          {displayNodes.length === 0 ? (
            <div className="org-empty">
              <Network size={48} />
              <h3>{searchResults !== null ? 'No results found' : 'No organisation units yet'}</h3>
              <p>
                {searchResults !== null
                  ? 'Try a different search term.'
                  : 'Create your first unit to get started with your organisation structure.'}
              </p>
              {searchResults === null && (
                <button className="btn btn-primary" onClick={handleCreateRoot}>
                  <Plus size={16} /> Create First Unit
                </button>
              )}
            </div>
          ) : searchResults !== null ? (
            <div className="search-results-list">
              {searchResults.map((u) => {
                const Icon = UNIT_TYPE_ICONS[u.unit_type] || Building2;
                return (
                  <div
                    key={u.id}
                    className={`search-result-item ${selectedUnit?.id === u.id ? 'selected' : ''}`}
                    onClick={() => handleSelect(u)}
                  >
                    <span className="tree-node-icon" style={{ color: UNIT_TYPE_COLORS[u.unit_type] }}>
                      <Icon size={16} />
                    </span>
                    <div className="search-result-info">
                      <span className="search-result-name">{u.name}</span>
                      {u.code && <span className="tree-node-code">{u.code}</span>}
                    </div>
                    <span className="tree-node-type-badge" style={{
                      backgroundColor: `${UNIT_TYPE_COLORS[u.unit_type]}15`,
                      color: UNIT_TYPE_COLORS[u.unit_type],
                    }}>
                      {UNIT_TYPE_LABELS[u.unit_type]}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="org-tree"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                // drop on empty space = make root
                e.preventDefault();
                setDragOverId(null);
                const dragNode = dragNodeRef.current;
                dragNodeRef.current = null;
                if (dragNode) {
                  organisationAPI.move(dragNode.id, null).then(() => {
                    showNotification(`"${dragNode.name}" moved to root`);
                    loadTree();
                  }).catch((err) => {
                    showNotification(err.response?.data?.error || 'Move failed', 'error');
                  });
                }
              }}
            >
              {displayNodes.map((node) => (
                <TreeNode
                  key={node.id}
                  node={node}
                  level={0}
                  selectedId={selectedUnit?.id}
                  onSelect={handleSelect}
                  onToggle={handleToggle}
                  expandedIds={expandedIds}
                  onDragStart={handleDragStart}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  dragOverId={dragOverId}
                />
              ))}
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selectedUnit && (
          <DetailPanel
            unit={selectedUnit}
            ancestors={ancestors}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onAddChild={handleAddChild}
            onClose={() => { setSelectedUnit(null); setAncestors([]); }}
          />
        )}
      </div>

      {/* Create / edit modal */}
      {showModal && (
        <UnitFormModal
          unit={editingUnit}
          parentId={parentIdForCreate}
          onSave={handleSave}
          onClose={() => { setShowModal(false); setEditingUnit(null); }}
        />
      )}
    </div>
  );
}

export default OrganisationPage;
