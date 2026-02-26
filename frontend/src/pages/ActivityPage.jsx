import React, { useState, useEffect, useCallback } from 'react';
import { eventsAPI } from '../services/api';
import { useAuth } from '../services/AuthContext';
import DataTable from '../components/DataTable';
import { Activity, RefreshCw } from 'lucide-react';

const EVENT_COLORS = {
  'auth':         'var(--primary)',
  'user':         '#7C3AED',
  'inventory':    '#0D9488',
  'sales':        '#2563EB',
  'purchasing':   '#D97706',
  'organisation': '#059669',
  'module':       '#6366F1',
};

function getEventColor(type) {
  const prefix = type?.split('.')[0] || '';
  return EVENT_COLORS[prefix] || 'var(--gray-400)';
}

export default function ActivityPage() {
  const { hasRole } = useAuth();
  const [events, setEvents] = useState([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const loadEvents = useCallback(async (pg = 1) => {
    setLoading(true);
    try {
      const params = { page: pg, per_page: 30 };
      if (filter) params.event_type = filter;
      const res = await eventsAPI.history(params);
      setEvents(res.data.events || []);
      setPage(res.data.page);
      setPages(res.data.pages);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to load events', err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { loadEvents(); }, [loadEvents]);

  const columns = [
    {
      key: 'created_at', label: 'Time',
      render: (v) => (
        <span style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
          {new Date(v).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'event_type', label: 'Event',
      render: (v) => (
        <span className="badge" style={{ background: getEventColor(v), color: '#fff', fontSize: 11 }}>
          {v}
        </span>
      ),
    },
    {
      key: 'data', label: 'Details',
      render: (v) => {
        if (!v || Object.keys(v).length === 0) return '—';
        const parts = Object.entries(v).slice(0, 3).map(([k, val]) => `${k}: ${val}`);
        return <span style={{ fontSize: 12, color: 'var(--gray-600)' }}>{parts.join(', ')}</span>;
      },
    },
    { key: 'source', label: 'Source', render: (v) => v || 'api' },
    {
      key: 'correlation_id', label: 'Correlation',
      render: (v) => v ? <code style={{ fontSize: 11 }}>{v.slice(0, 8)}</code> : '—',
    },
  ];

  return (
    <div>
      <header className="dashboard-header">
        <div>
          <h1><Activity size={22} style={{ verticalAlign: 'middle', marginRight: 8 }} />Activity Feed</h1>
          <p className="header-subtitle">{total} events recorded</p>
        </div>
        <div className="header-actions">
          <input
            type="text"
            placeholder="Filter by event type…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--gray-200)', fontSize: 13 }}
          />
          <button className="btn btn-secondary" onClick={() => loadEvents(page)}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </header>

      <div className="card">
        {loading ? (
          <div style={{ padding: 32, textAlign: 'center' }}><div className="loading-spinner" /></div>
        ) : (
          <>
            <DataTable columns={columns} data={events} emptyMessage="No events found" />
            {pages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: '12px 0' }}>
                <button className="btn btn-sm btn-secondary" disabled={page <= 1} onClick={() => loadEvents(page - 1)}>Previous</button>
                <span style={{ padding: '4px 8px', fontSize: 13 }}>Page {page} of {pages}</span>
                <button className="btn btn-sm btn-secondary" disabled={page >= pages} onClick={() => loadEvents(page + 1)}>Next</button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
