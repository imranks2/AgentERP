import React, { useState, useEffect, useCallback } from 'react';
import { aiAdvancedAPI } from '../services/api';
import {
  Lightbulb, CheckCircle, X, AlertTriangle, TrendingUp, RefreshCw,
  ChevronDown, ChevronUp, Zap, Info,
} from 'lucide-react';

const PRIORITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

const TYPE_ICONS = {
  action: <Zap size={16} />,
  insight: <Info size={16} />,
  warning: <AlertTriangle size={16} />,
  automation: <TrendingUp size={16} />,
};

function AISuggestionsSidebar({ isOpen, onClose }) {
  const [suggestions, setSuggestions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);

  const loadSuggestions = useCallback(async () => {
    try {
      setLoading(true);
      const [sugRes, statRes] = await Promise.all([
        aiAdvancedAPI.listSuggestions({ status: 'pending' }).catch(() => ({ data: { suggestions: [] } })),
        aiAdvancedAPI.suggestionStats().catch(() => ({ data: {} })),
      ]);
      setSuggestions(sugRes.data.suggestions || []);
      setStats(statRes.data || null);
    } catch {
      /* silently fail */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { if (isOpen) loadSuggestions(); }, [isOpen, loadSuggestions]);

  const generate = async () => {
    try {
      await aiAdvancedAPI.generateSuggestions();
      loadSuggestions();
    } catch { /* ignore */ }
  };

  const accept = async (id) => {
    try {
      await aiAdvancedAPI.acceptSuggestion(id);
      setSuggestions(s => s.filter(x => x.id !== id));
    } catch { /* ignore */ }
  };

  const dismiss = async (id) => {
    try {
      await aiAdvancedAPI.dismissSuggestion(id);
      setSuggestions(s => s.filter(x => x.id !== id));
    } catch { /* ignore */ }
  };

  if (!isOpen) return null;

  return (
    <div className="ai-sidebar" style={styles.sidebar}>
      <div style={styles.header}>
        <div style={styles.headerTitle}>
          <Lightbulb size={18} />
          <span>AI Suggestions</span>
          {suggestions.length > 0 && (
            <span style={styles.badge}>{suggestions.length}</span>
          )}
        </div>
        <div style={styles.headerActions}>
          <button style={styles.iconBtn} onClick={generate} title="Generate suggestions">
            <RefreshCw size={16} />
          </button>
          <button style={styles.iconBtn} onClick={onClose}>
            <X size={16} />
          </button>
        </div>
      </div>

      {stats && (
        <div style={styles.statsBar}>
          <span>Acceptance rate: <strong>{Math.round((stats.acceptance_rate || 0) * 100)}%</strong></span>
          <span>Total: {stats.total_suggestions || 0}</span>
        </div>
      )}

      <div style={styles.list}>
        {loading ? (
          <div style={styles.empty}>Loading...</div>
        ) : suggestions.length === 0 ? (
          <div style={styles.empty}>
            <Lightbulb size={32} style={{ opacity: 0.3 }} />
            <p>No pending suggestions</p>
            <button style={styles.generateBtn} onClick={generate}>
              Generate suggestions
            </button>
          </div>
        ) : (
          suggestions.map(s => (
            <div key={s.id} style={styles.card}>
              <div style={styles.cardHeader} onClick={() => setExpanded(expanded === s.id ? null : s.id)}>
                <div style={styles.cardLeft}>
                  <span style={{ color: PRIORITY_COLORS[s.priority] || '#888' }}>
                    {TYPE_ICONS[s.suggestion_type] || <Info size={16} />}
                  </span>
                  <span style={styles.cardTitle}>{s.title}</span>
                </div>
                <div style={styles.cardRight}>
                  <span style={styles.confidenceBadge}>
                    {Math.round((s.confidence || 0) * 100)}%
                  </span>
                  {expanded === s.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </div>
              </div>

              {expanded === s.id && (
                <div style={styles.cardBody}>
                  {s.description && <p style={styles.desc}>{s.description}</p>}
                  {s.reasoning && (
                    <div style={styles.reasoning}>
                      <strong>Why: </strong>{s.reasoning}
                    </div>
                  )}
                  <div style={styles.cardActions}>
                    <button style={styles.acceptBtn} onClick={() => accept(s.id)}>
                      <CheckCircle size={14} /> Accept
                    </button>
                    <button style={styles.dismissBtn} onClick={() => dismiss(s.id)}>
                      <X size={14} /> Dismiss
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

const styles = {
  sidebar: {
    position: 'fixed', right: 0, top: 0, bottom: 0, width: 360,
    background: 'var(--bg-primary, #fff)', borderLeft: '1px solid var(--border, #e2e8f0)',
    zIndex: 1100, display: 'flex', flexDirection: 'column',
    boxShadow: '-4px 0 12px rgba(0,0,0,0.08)',
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '16px', borderBottom: '1px solid var(--border, #e2e8f0)',
  },
  headerTitle: { display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: 15 },
  headerActions: { display: 'flex', gap: 4 },
  iconBtn: {
    background: 'none', border: 'none', cursor: 'pointer', padding: 4,
    borderRadius: 4, color: 'var(--text-secondary, #64748b)',
  },
  badge: {
    background: 'var(--primary, #3b82f6)', color: '#fff', borderRadius: 10,
    fontSize: 11, padding: '2px 7px', fontWeight: 600,
  },
  statsBar: {
    display: 'flex', justifyContent: 'space-between', padding: '8px 16px',
    fontSize: 12, color: 'var(--text-secondary, #64748b)',
    borderBottom: '1px solid var(--border, #e2e8f0)',
  },
  list: { flex: 1, overflowY: 'auto', padding: 12 },
  empty: { textAlign: 'center', padding: 40, color: 'var(--text-secondary, #94a3b8)' },
  generateBtn: {
    marginTop: 12, padding: '8px 16px', borderRadius: 6,
    background: 'var(--primary, #3b82f6)', color: '#fff', border: 'none',
    cursor: 'pointer', fontSize: 13,
  },
  card: {
    borderRadius: 8, border: '1px solid var(--border, #e2e8f0)',
    marginBottom: 8, overflow: 'hidden',
  },
  cardHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '10px 12px', cursor: 'pointer',
  },
  cardLeft: { display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 },
  cardRight: { display: 'flex', alignItems: 'center', gap: 6 },
  cardTitle: { fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  confidenceBadge: {
    fontSize: 11, fontWeight: 600, padding: '2px 6px', borderRadius: 4,
    background: 'var(--bg-secondary, #f1f5f9)',
  },
  cardBody: { padding: '0 12px 12px', fontSize: 13 },
  desc: { margin: '0 0 8px', color: 'var(--text-secondary, #64748b)' },
  reasoning: {
    padding: '8px 10px', borderRadius: 6,
    background: 'var(--bg-secondary, #f8fafc)', fontSize: 12,
    marginBottom: 8, color: 'var(--text-secondary, #64748b)',
  },
  cardActions: { display: 'flex', gap: 8 },
  acceptBtn: {
    display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px',
    borderRadius: 6, border: 'none', background: '#22c55e', color: '#fff',
    cursor: 'pointer', fontSize: 12, fontWeight: 500,
  },
  dismissBtn: {
    display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px',
    borderRadius: 6, border: '1px solid var(--border, #e2e8f0)', background: 'none',
    cursor: 'pointer', fontSize: 12, color: 'var(--text-secondary, #64748b)',
  },
};

export default AISuggestionsSidebar;
