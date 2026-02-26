import React, { useState, useEffect, useCallback } from 'react';
import { accountingAPI } from '../services/api';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import TabBar from '../components/TabBar';
import StatCards from '../components/StatCards';
import Alert from '../components/Alert';
import PageHeader from '../components/PageHeader';
import {
  BookOpen, Plus, Edit3, Trash2, CheckCircle, RotateCcw,
  DollarSign, TrendingUp, FileText,
} from 'lucide-react';
import '../styles/erp.css';

function AccountingPage() {
  const [tab, setTab] = useState('accounts');
  const [accounts, setAccounts] = useState([]);
  const [journals, setJournals] = useState([]);
  const [taxRates, setTaxRates] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [stats, setStats] = useState(null);
  const [trialBalance, setTrialBalance] = useState([]);
  const [profitLoss, setProfitLoss] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [acctRes, jeRes, taxRes, currRes, statRes] = await Promise.all([
        accountingAPI.listAccounts({ search }).catch(() => ({ data: { accounts: [] } })),
        accountingAPI.listJournalEntries({}).catch(() => ({ data: { entries: [] } })),
        accountingAPI.listTaxRates().catch(() => ({ data: { tax_rates: [] } })),
        accountingAPI.listCurrencies().catch(() => ({ data: { currencies: [] } })),
        accountingAPI.stats().catch(() => ({ data: {} })),
      ]);
      setAccounts(acctRes.data.accounts || []);
      setJournals(jeRes.data.entries || []);
      setTaxRates(taxRes.data.tax_rates || []);
      setCurrencies(currRes.data.currencies || []);
      setStats(statRes.data || {});
    } catch {
      setError('Failed to load accounting data');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { loadData(); }, [loadData]);

  const loadReports = useCallback(async () => {
    try {
      const [tbRes, plRes] = await Promise.all([
        accountingAPI.trialBalance({}).catch(() => ({ data: { trial_balance: [] } })),
        accountingAPI.profitAndLoss({}).catch(() => ({ data: {} })),
      ]);
      setTrialBalance(tbRes.data.trial_balance || []);
      setProfitLoss(plRes.data || null);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { if (tab === 'reports') loadReports(); }, [tab, loadReports]);

  /* ── Account form ──────────────────────────── */
  const accountFields = [
    { name: 'code', label: 'Code', type: 'text', required: true },
    { name: 'name', label: 'Name', type: 'text', required: true },
    { name: 'account_type', label: 'Type', type: 'select', required: true,
      options: [
        { value: 'asset', label: 'Asset' },
        { value: 'liability', label: 'Liability' },
        { value: 'equity', label: 'Equity' },
        { value: 'revenue', label: 'Revenue' },
        { value: 'expense', label: 'Expense' },
      ],
    },
    { name: 'description', label: 'Description', type: 'textarea' },
  ];

  const handleSaveAccount = async (formData) => {
    try {
      if (editItem) {
        await accountingAPI.updateAccount(editItem.id, formData);
        setSuccess('Account updated');
      } else {
        await accountingAPI.createAccount(formData);
        setSuccess('Account created');
      }
      setShowForm(false);
      setEditItem(null);
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save account');
    }
  };

  const handleDeleteAccount = async (acct) => {
    if (!window.confirm(`Delete account ${acct.code}?`)) return;
    try {
      await accountingAPI.deleteAccount(acct.id);
      setSuccess('Account deleted');
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Delete failed');
    }
  };

  const handlePostJE = async (je) => {
    try {
      await accountingAPI.postJournalEntry(je.id);
      setSuccess('Journal entry posted');
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Post failed');
    }
  };

  const handleReverseJE = async (je) => {
    try {
      await accountingAPI.reverseJournalEntry(je.id);
      setSuccess('Journal entry reversed');
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Reverse failed');
    }
  };

  const tabs = [
    { key: 'accounts', label: 'Chart of Accounts', icon: <BookOpen size={16} /> },
    { key: 'journals', label: 'Journal Entries', icon: <FileText size={16} /> },
    { key: 'taxrates', label: 'Tax Rates', icon: <DollarSign size={16} /> },
    { key: 'reports', label: 'Reports', icon: <TrendingUp size={16} /> },
  ];

  const accountCols = [
    { key: 'code', label: 'Code', sortable: true },
    { key: 'name', label: 'Name', sortable: true },
    { key: 'account_type', label: 'Type', render: (v) => <span className="badge badge-info">{v}</span> },
    { key: 'currency', label: 'Currency' },
    {
      key: 'actions', label: '', render: (_, row) => (
        <div className="action-btns">
          <button className="btn btn-sm" onClick={() => { setEditItem(row); setShowForm(true); }}><Edit3 size={14} /></button>
          <button className="btn btn-sm btn-danger" onClick={() => handleDeleteAccount(row)}><Trash2 size={14} /></button>
        </div>
      ),
    },
  ];

  const journalCols = [
    { key: 'number', label: 'Number', sortable: true },
    { key: 'date', label: 'Date', sortable: true },
    { key: 'description', label: 'Description' },
    { key: 'total_debit', label: 'Debit', render: (v) => v?.toFixed(2) },
    { key: 'total_credit', label: 'Credit', render: (v) => v?.toFixed(2) },
    { key: 'status', label: 'Status', render: (v) => (
      <span className={`badge ${v === 'posted' ? 'badge-success' : v === 'reversed' ? 'badge-warning' : 'badge-secondary'}`}>{v}</span>
    )},
    {
      key: 'actions', label: '', render: (_, row) => (
        <div className="action-btns">
          {row.status === 'draft' && <button className="btn btn-sm btn-success" onClick={() => handlePostJE(row)} title="Post"><CheckCircle size={14} /></button>}
          {row.status === 'posted' && <button className="btn btn-sm btn-warning" onClick={() => handleReverseJE(row)} title="Reverse"><RotateCcw size={14} /></button>}
        </div>
      ),
    },
  ];

  const taxCols = [
    { key: 'code', label: 'Code' }, { key: 'name', label: 'Name' },
    { key: 'rate', label: 'Rate', render: (v) => `${(v * 100).toFixed(1)}%` },
    { key: 'tax_type', label: 'Type' }, { key: 'jurisdiction', label: 'Jurisdiction' },
  ];

  return (
    <div className="erp-page">
      <PageHeader title="Accounting" icon={<BookOpen />}
        action={tab === 'accounts' ? { label: 'New Account', icon: <Plus size={16} />, onClick: () => { setEditItem(null); setShowForm(true); } } : null}
      />
      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {stats && (
        <StatCards cards={[
          { label: 'Accounts', value: stats.total_accounts || 0 },
          { label: 'Journal Entries', value: stats.total_journal_entries || 0 },
          { label: 'Posted', value: stats.posted_entries || 0 },
          { label: 'Drafts', value: stats.draft_entries || 0 },
        ]} />
      )}

      <TabBar tabs={tabs} active={tab} onChange={setTab} />

      {tab === 'accounts' && (
        <>
          <div className="toolbar"><input className="search-input" placeholder="Search accounts…" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
          <DataTable columns={accountCols} data={accounts} loading={loading} emptyMessage="No accounts yet" />
        </>
      )}

      {tab === 'journals' && (
        <DataTable columns={journalCols} data={journals} loading={loading} emptyMessage="No journal entries" />
      )}

      {tab === 'taxrates' && (
        <DataTable columns={taxCols} data={taxRates} loading={loading} emptyMessage="No tax rates" />
      )}

      {tab === 'reports' && (
        <div className="reports-section">
          <h3>Profit & Loss</h3>
          {profitLoss ? (
            <div className="report-summary">
              <div className="report-row"><span>Revenue</span><strong>{profitLoss.revenue?.toFixed(2)}</strong></div>
              <div className="report-row"><span>Expenses</span><strong>{profitLoss.expense?.toFixed(2)}</strong></div>
              <div className="report-row total"><span>Net Income</span><strong>{profitLoss.net_income?.toFixed(2)}</strong></div>
            </div>
          ) : <p className="text-muted">No data</p>}

          <h3>Trial Balance</h3>
          {trialBalance.length > 0 ? (
            <DataTable columns={[
              { key: 'code', label: 'Code' }, { key: 'name', label: 'Account' },
              { key: 'account_type', label: 'Type' },
              { key: 'total_debit', label: 'Debit', render: (v) => v?.toFixed(2) },
              { key: 'total_credit', label: 'Credit', render: (v) => v?.toFixed(2) },
              { key: 'balance', label: 'Balance', render: (v) => v?.toFixed(2) },
            ]} data={trialBalance} />
          ) : <p className="text-muted">No data</p>}
        </div>
      )}

      {showForm && (
        <Modal title={editItem ? 'Edit Account' : 'New Account'} onClose={() => { setShowForm(false); setEditItem(null); }}>
          <DynamicForm fields={accountFields} initialValues={editItem || {}} onSubmit={handleSaveAccount} submitLabel={editItem ? 'Update' : 'Create'} />
        </Modal>
      )}
    </div>
  );
}

export default AccountingPage;
