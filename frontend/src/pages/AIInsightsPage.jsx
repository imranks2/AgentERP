import React, { useState, useEffect, useCallback } from 'react';
import { aiAdvancedAPI } from '../services/api';
import DataTable from '../components/DataTable';
import TabBar from '../components/TabBar';
import StatCards from '../components/StatCards';
import Alert from '../components/Alert';
import PageHeader from '../components/PageHeader';
import {
  Brain, Lightbulb, Workflow, Database, Cpu,
  CheckCircle, XCircle, Play, RefreshCw,
} from 'lucide-react';
import '../styles/erp.css';

function AIInsightsPage() {
  const [tab, setTab] = useState('suggestions');
  const [suggestions, setSuggestions] = useState([]);
  const [actions, setActions] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [models, setModels] = useState([]);
  const [trainingStats, setTrainingStats] = useState(null);
  const [actionStats, setActionStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [sugRes, actRes, patRes, wfRes, dsRes, modRes, tsRes, asRes] = await Promise.all([
        aiAdvancedAPI.listSuggestions({}).catch(() => ({ data: { suggestions: [] } })),
        aiAdvancedAPI.listActions({}).catch(() => ({ data: { actions: [] } })),
        aiAdvancedAPI.listPatterns({}).catch(() => ({ data: { patterns: [] } })),
        aiAdvancedAPI.listWorkflows({}).catch(() => ({ data: { workflows: [] } })),
        aiAdvancedAPI.listDatasets({}).catch(() => ({ data: { datasets: [] } })),
        aiAdvancedAPI.listModels({}).catch(() => ({ data: { models: [] } })),
        aiAdvancedAPI.trainingStats().catch(() => ({ data: {} })),
        aiAdvancedAPI.actionStats().catch(() => ({ data: {} })),
      ]);
      setSuggestions(sugRes.data.suggestions || []);
      setActions(actRes.data.actions || []);
      setPatterns(patRes.data.patterns || []);
      setWorkflows(wfRes.data.workflows || []);
      setDatasets(dsRes.data.datasets || []);
      setModels(modRes.data.models || []);
      setTrainingStats(tsRes.data || {});
      setActionStats(asRes.data || {});
    } catch {
      setError('Failed to load AI data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAcceptSuggestion = async (s) => {
    try { await aiAdvancedAPI.acceptSuggestion(s.id); setSuccess('Suggestion accepted'); loadData(); }
    catch { setError('Failed to accept'); }
  };
  const handleDismissSuggestion = async (s) => {
    try { await aiAdvancedAPI.dismissSuggestion(s.id); setSuccess('Dismissed'); loadData(); }
    catch { setError('Failed to dismiss'); }
  };
  const handleApproveAction = async (a) => {
    try { await aiAdvancedAPI.approveAction(a.id); setSuccess('Action approved'); loadData(); }
    catch { setError('Failed to approve'); }
  };
  const handleRejectAction = async (a) => {
    try { await aiAdvancedAPI.rejectAction(a.id); setSuccess('Action rejected'); loadData(); }
    catch { setError('Failed to reject'); }
  };
  const handleExport = async () => {
    try { await aiAdvancedAPI.exportTrainingData(); setSuccess('Training data exported'); loadData(); }
    catch { setError('Export failed'); }
  };
  const handleActivateModel = async (m) => {
    try { await aiAdvancedAPI.activateModel(m.id); setSuccess('Model activated'); loadData(); }
    catch { setError('Activation failed'); }
  };
  const handleToggleWorkflow = async (wf) => {
    try { await aiAdvancedAPI.toggleWorkflow(wf.id); loadData(); }
    catch { setError('Toggle failed'); }
  };
  const handleDetectPatterns = async () => {
    try { await aiAdvancedAPI.detectPatterns(); setSuccess('Pattern detection complete'); loadData(); }
    catch { setError('Detection failed'); }
  };
  const handleGenerate = async () => {
    try { await aiAdvancedAPI.generateSuggestions(); setSuccess('Suggestions generated'); loadData(); }
    catch { setError('Generation failed'); }
  };

  const tabs = [
    { key: 'suggestions', label: 'Suggestions', icon: <Lightbulb size={16} /> },
    { key: 'actions', label: 'Agent Actions', icon: <Play size={16} /> },
    { key: 'patterns', label: 'Patterns & Workflows', icon: <Workflow size={16} /> },
    { key: 'training', label: 'Training Pipeline', icon: <Database size={16} /> },
  ];

  const statusBadge = (s) => {
    const m = { pending: 'badge-warning', accepted: 'badge-success', dismissed: 'badge-secondary',
      executed: 'badge-info', proposed: 'badge-warning', approved: 'badge-success',
      rejected: 'badge-danger', failed: 'badge-danger', detected: 'badge-info',
      activated: 'badge-success', active: 'badge-success', training: 'badge-warning',
      evaluating: 'badge-info', retired: 'badge-secondary', ready: 'badge-success',
    };
    return m[s] || 'badge-secondary';
  };

  const sugCols = [
    { key: 'title', label: 'Title', sortable: true },
    { key: 'suggestion_type', label: 'Type' },
    { key: 'category', label: 'Category' },
    { key: 'confidence', label: 'Confidence', render: (v) => `${Math.round((v || 0) * 100)}%` },
    { key: 'priority', label: 'Priority' },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
    { key: 'actions', label: '', render: (_, row) => row.status === 'pending' ? (
      <div className="action-btns">
        <button className="btn btn-sm btn-success" onClick={() => handleAcceptSuggestion(row)}><CheckCircle size={14} /></button>
        <button className="btn btn-sm" onClick={() => handleDismissSuggestion(row)}><XCircle size={14} /></button>
      </div>
    ) : null },
  ];

  const actCols = [
    { key: 'action_type', label: 'Type', sortable: true },
    { key: 'description', label: 'Description' },
    { key: 'risk_level', label: 'Risk' },
    { key: 'confidence', label: 'Confidence', render: (v) => `${Math.round((v || 0) * 100)}%` },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
    { key: 'actions', label: '', render: (_, row) => row.status === 'proposed' ? (
      <div className="action-btns">
        <button className="btn btn-sm btn-success" onClick={() => handleApproveAction(row)} title="Approve"><CheckCircle size={14} /></button>
        <button className="btn btn-sm btn-danger" onClick={() => handleRejectAction(row)} title="Reject"><XCircle size={14} /></button>
      </div>
    ) : null },
  ];

  const patCols = [
    { key: 'name', label: 'Pattern', sortable: true },
    { key: 'frequency', label: 'Frequency' },
    { key: 'confidence', label: 'Confidence', render: (v) => `${Math.round((v || 0) * 100)}%` },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
  ];

  const wfCols = [
    { key: 'name', label: 'Workflow', sortable: true },
    { key: 'trigger_event', label: 'Trigger' },
    { key: 'execution_count', label: 'Runs' },
    { key: 'is_active', label: 'Active', render: (v) => <span className={`badge ${v ? 'badge-success' : 'badge-secondary'}`}>{v ? 'Yes' : 'No'}</span> },
    { key: 'actions', label: '', render: (_, row) => (
      <button className="btn btn-sm" onClick={() => handleToggleWorkflow(row)}>{row.is_active ? 'Disable' : 'Enable'}</button>
    )},
  ];

  const dsCols = [
    { key: 'version', label: 'Version' },
    { key: 'record_count', label: 'Records' },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
    { key: 'created_at', label: 'Created', render: (v) => v ? new Date(v).toLocaleDateString() : '' },
  ];

  const modelCols = [
    { key: 'version', label: 'Version' },
    { key: 'model_type', label: 'Type' },
    { key: 'status', label: 'Status', render: (v) => <span className={`badge ${statusBadge(v)}`}>{v}</span> },
    { key: 'metrics', label: 'Accuracy', render: (v) => v?.accuracy ? `${(v.accuracy * 100).toFixed(1)}%` : '—' },
    { key: 'is_active', label: 'Active', render: (v) => v ? '✓' : '' },
    { key: 'actions', label: '', render: (_, row) => !row.is_active ? (
      <button className="btn btn-sm btn-success" onClick={() => handleActivateModel(row)}>Activate</button>
    ) : null },
  ];

  return (
    <div className="erp-page">
      <PageHeader title="AI Intelligence" icon={<Brain />} />
      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {trainingStats && (
        <StatCards cards={[
          { label: 'Total Interactions', value: trainingStats.total_interactions || 0 },
          { label: 'Feedback Rate', value: `${Math.round((trainingStats.feedback_rate || 0) * 100)}%` },
          { label: 'Satisfaction', value: `${Math.round((trainingStats.satisfaction_rate || 0) * 100)}%` },
          { label: 'Active Models', value: trainingStats.active_models || 0 },
        ]} />
      )}

      <TabBar tabs={tabs} active={tab} onChange={setTab} />

      {tab === 'suggestions' && (
        <>
          <div className="toolbar">
            <button className="btn btn-sm btn-primary" onClick={handleGenerate}>
              <RefreshCw size={14} /> Generate Suggestions
            </button>
          </div>
          <DataTable columns={sugCols} data={suggestions} loading={loading} emptyMessage="No suggestions" />
        </>
      )}

      {tab === 'actions' && (
        <DataTable columns={actCols} data={actions} loading={loading} emptyMessage="No agent actions" />
      )}

      {tab === 'patterns' && (
        <>
          <div className="toolbar">
            <button className="btn btn-sm btn-primary" onClick={handleDetectPatterns}>
              <Cpu size={14} /> Detect Patterns
            </button>
          </div>
          <h3 style={{ marginTop: 16 }}>Detected Patterns</h3>
          <DataTable columns={patCols} data={patterns} loading={loading} emptyMessage="No patterns detected" />
          <h3 style={{ marginTop: 24 }}>Automated Workflows</h3>
          <DataTable columns={wfCols} data={workflows} loading={loading} emptyMessage="No workflows" />
        </>
      )}

      {tab === 'training' && (
        <>
          <div className="toolbar">
            <button className="btn btn-sm btn-primary" onClick={handleExport}>
              <Database size={14} /> Export Training Data
            </button>
          </div>
          <h3 style={{ marginTop: 16 }}>Datasets</h3>
          <DataTable columns={dsCols} data={datasets} loading={loading} emptyMessage="No datasets" />
          <h3 style={{ marginTop: 24 }}>Model Versions</h3>
          <DataTable columns={modelCols} data={models} loading={loading} emptyMessage="No models" />
        </>
      )}
    </div>
  );
}

export default AIInsightsPage;
