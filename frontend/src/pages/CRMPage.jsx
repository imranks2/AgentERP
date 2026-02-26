import React, { useState, useEffect, useCallback } from 'react';
import { crmAPI } from '../services/api';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import TabBar from '../components/TabBar';
import StatCards from '../components/StatCards';
import Alert from '../components/Alert';
import PageHeader from '../components/PageHeader';
import {
  Target, Plus, Edit3, Trash2, TrendingUp,
  Phone, Mail, Calendar, Users,
} from 'lucide-react';
import '../styles/erp.css';

function CRMPage() {
  const [tab, setTab] = useState('leads');
  const [leads, setLeads] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [activities, setActivities] = useState([]);
  const [pipelineData, setPipelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [formType, setFormType] = useState('lead');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [leadRes, oppRes, actRes, pipeRes] = await Promise.all([
        crmAPI.listLeads({ search }).catch(() => ({ data: { leads: [] } })),
        crmAPI.listOpportunities({ search }).catch(() => ({ data: { opportunities: [] } })),
        crmAPI.listActivities({}).catch(() => ({ data: { activities: [] } })),
        crmAPI.pipelineStats().catch(() => ({ data: {} })),
      ]);
      setLeads(leadRes.data.leads || []);
      setOpportunities(oppRes.data.opportunities || []);
      setActivities(actRes.data.activities || []);
      setPipelineData(pipeRes.data || null);
    } catch {
      setError('Failed to load CRM data');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { loadData(); }, [loadData]);

  /* ── Lead form ─────────────────────────────── */
  const leadFields = [
    { name: 'name', label: 'Name', type: 'text', required: true },
    { name: 'email', label: 'Email', type: 'email' },
    { name: 'phone', label: 'Phone', type: 'text' },
    { name: 'company', label: 'Company', type: 'text' },
    { name: 'source', label: 'Source', type: 'select', options: [
      { value: 'web', label: 'Web' }, { value: 'referral', label: 'Referral' },
      { value: 'campaign', label: 'Campaign' }, { value: 'other', label: 'Other' },
    ]},
    { name: 'status', label: 'Status', type: 'select', options: [
      { value: 'new', label: 'New' }, { value: 'contacted', label: 'Contacted' },
      { value: 'qualified', label: 'Qualified' }, { value: 'lost', label: 'Lost' },
    ]},
    { name: 'score', label: 'Score', type: 'number' },
    { name: 'notes', label: 'Notes', type: 'textarea' },
  ];

  const oppFields = [
    { name: 'title', label: 'Title', type: 'text', required: true },
    { name: 'value', label: 'Value', type: 'number' },
    { name: 'currency', label: 'Currency', type: 'text' },
    { name: 'stage', label: 'Stage', type: 'select', options: [
      { value: 'prospecting', label: 'Prospecting' }, { value: 'proposal', label: 'Proposal' },
      { value: 'negotiation', label: 'Negotiation' }, { value: 'won', label: 'Won' },
      { value: 'lost', label: 'Lost' },
    ]},
    { name: 'probability', label: 'Probability (%)', type: 'number' },
    { name: 'expected_close_date', label: 'Expected Close', type: 'date' },
    { name: 'notes', label: 'Notes', type: 'textarea' },
  ];

  const handleSaveLead = async (formData) => {
    try {
      if (editItem) { await crmAPI.updateLead(editItem.id, formData); setSuccess('Lead updated'); }
      else { await crmAPI.createLead(formData); setSuccess('Lead created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Failed to save lead'); }
  };

  const handleSaveOpp = async (formData) => {
    try {
      if (editItem) { await crmAPI.updateOpportunity(editItem.id, formData); setSuccess('Opportunity updated'); }
      else { await crmAPI.createOpportunity(formData); setSuccess('Opportunity created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Failed to save opportunity'); }
  };

  const handleDeleteLead = async (lead) => {
    if (!window.confirm(`Delete lead "${lead.name}"?`)) return;
    try { await crmAPI.deleteLead(lead.id); setSuccess('Lead deleted'); loadData(); }
    catch (err) { setError(err.response?.data?.error || 'Delete failed'); }
  };

  const handleDeleteOpp = async (opp) => {
    if (!window.confirm(`Delete opportunity "${opp.title}"?`)) return;
    try { await crmAPI.deleteOpportunity(opp.id); setSuccess('Deleted'); loadData(); }
    catch (err) { setError(err.response?.data?.error || 'Delete failed'); }
  };

  const openNew = (type) => { setFormType(type); setEditItem(null); setShowForm(true); };

  const tabs = [
    { key: 'leads', label: 'Leads', icon: <Users size={16} /> },
    { key: 'opportunities', label: 'Opportunities', icon: <TrendingUp size={16} /> },
    { key: 'activities', label: 'Activities', icon: <Calendar size={16} /> },
    { key: 'pipeline', label: 'Pipeline', icon: <Target size={16} /> },
  ];

  const stageColor = (s) => s === 'won' ? 'badge-success' : s === 'lost' ? 'badge-danger' : 'badge-info';
  const statusColor = (s) => s === 'qualified' ? 'badge-success' : s === 'lost' ? 'badge-danger' : s === 'contacted' ? 'badge-info' : 'badge-secondary';

  const leadCols = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'email', label: 'Email' }, { key: 'company', label: 'Company' },
    { key: 'source', label: 'Source' },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusColor(v)}`}>{v}</span> },
    { key: 'score', label: 'Score' },
    { key: 'actions', label: '', render: (_, row) => (
      <div className="action-btns">
        <button className="btn btn-sm" onClick={() => { setFormType('lead'); setEditItem(row); setShowForm(true); }}><Edit3 size={14} /></button>
        <button className="btn btn-sm btn-danger" onClick={() => handleDeleteLead(row)}><Trash2 size={14} /></button>
      </div>
    )},
  ];

  const oppCols = [
    { key: 'title', label: 'Title', sortable: true },
    { key: 'value', label: 'Value', render: (v, row) => `${row.currency || 'USD'} ${(v || 0).toLocaleString()}` },
    { key: 'stage', label: 'Stage', render: (v) => <span className={`badge ${stageColor(v)}`}>{v}</span> },
    { key: 'probability', label: 'Prob.', render: (v) => `${v}%` },
    { key: 'expected_close_date', label: 'Close Date' },
    { key: 'actions', label: '', render: (_, row) => (
      <div className="action-btns">
        <button className="btn btn-sm" onClick={() => { setFormType('opportunity'); setEditItem(row); setShowForm(true); }}><Edit3 size={14} /></button>
        <button className="btn btn-sm btn-danger" onClick={() => handleDeleteOpp(row)}><Trash2 size={14} /></button>
      </div>
    )},
  ];

  const actCols = [
    { key: 'activity_type', label: 'Type', render: (v) => {
      const icon = v === 'call' ? <Phone size={14} /> : v === 'email' ? <Mail size={14} /> : <Calendar size={14} />;
      return <span className="activity-type">{icon} {v}</span>;
    }},
    { key: 'subject', label: 'Subject' },
    { key: 'date', label: 'Date', render: (v) => v ? new Date(v).toLocaleDateString() : '' },
  ];

  return (
    <div className="erp-page">
      <PageHeader title="CRM" icon={<Target />}
        action={tab === 'leads' ? { label: 'New Lead', icon: <Plus size={16} />, onClick: () => openNew('lead') }
          : tab === 'opportunities' ? { label: 'New Opportunity', icon: <Plus size={16} />, onClick: () => openNew('opportunity') }
          : null}
      />
      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {pipelineData && (
        <StatCards cards={[
          { label: 'Total Leads', value: pipelineData.total_leads || 0 },
          { label: 'Open Opps', value: pipelineData.total_opportunities || 0 },
          { label: 'Pipeline Value', value: `$${(pipelineData.total_pipeline_value || 0).toLocaleString()}` },
        ]} />
      )}

      <TabBar tabs={tabs} active={tab} onChange={setTab} />

      {tab === 'leads' && (
        <>
          <div className="toolbar"><input className="search-input" placeholder="Search leads…" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
          <DataTable columns={leadCols} data={leads} loading={loading} emptyMessage="No leads yet" />
        </>
      )}

      {tab === 'opportunities' && (
        <DataTable columns={oppCols} data={opportunities} loading={loading} emptyMessage="No opportunities" />
      )}

      {tab === 'activities' && (
        <DataTable columns={actCols} data={activities} loading={loading} emptyMessage="No activities" />
      )}

      {tab === 'pipeline' && pipelineData?.stages && (
        <div className="pipeline-view">
          {Object.entries(pipelineData.stages).map(([stage, info]) => (
            <div key={stage} className="pipeline-stage">
              <h4>{stage}</h4>
              <div className="pipeline-metrics">
                <span>{info.count} deals</span>
                <strong>${info.total_value?.toLocaleString()}</strong>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <Modal title={editItem ? `Edit ${formType}` : `New ${formType}`} onClose={() => { setShowForm(false); setEditItem(null); }}>
          <DynamicForm
            fields={formType === 'lead' ? leadFields : oppFields}
            initialValues={editItem || {}}
            onSubmit={formType === 'lead' ? handleSaveLead : handleSaveOpp}
            submitLabel={editItem ? 'Update' : 'Create'}
          />
        </Modal>
      )}
    </div>
  );
}

export default CRMPage;
