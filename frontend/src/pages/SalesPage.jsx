import React, { useState, useEffect, useCallback } from 'react';
import { salesAPI, inventoryAPI } from '../services/api';
import analytics from '../services/analytics';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import TabBar from '../components/TabBar';
import StatCards from '../components/StatCards';
import Alert from '../components/Alert';
import PageHeader from '../components/PageHeader';
import LineItems from '../components/LineItems';
import { formatCurrency } from '../utils/formatters';
import { STATUS_CONFIG, PAYMENT_METHODS } from '../utils/constants';
import {
  Plus, Edit3, Eye, FileText, DollarSign,
  Users, ArrowRight, X,
} from 'lucide-react';
import '../styles/erp.css';

function SalesPage() {
  const [tab, setTab] = useState('quotations');
  const [customers, setCustomers] = useState([]);
  const [quotations, setQuotations] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [viewItem, setViewItem] = useState(null);
  const [paymentModal, setPaymentModal] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [custRes, qtRes, invRes, prodRes, whRes, statRes] = await Promise.all([
        salesAPI.listCustomers({}).catch(() => ({ data: { customers: [] } })),
        salesAPI.listQuotations({}).catch(() => ({ data: { quotations: [] } })),
        salesAPI.listInvoices({}).catch(() => ({ data: { invoices: [] } })),
        inventoryAPI.listProducts({}).catch(() => ({ data: { products: [] } })),
        inventoryAPI.listWarehouses().catch(() => ({ data: { warehouses: [] } })),
        salesAPI.stats().catch(() => ({ data: { stats: {} } })),
      ]);
      setCustomers(custRes.data.customers || []);
      setQuotations(qtRes.data.quotations || []);
      setInvoices(invRes.data.invoices || []);
      setProducts(prodRes.data.products || []);
      setWarehouses(whRes.data.warehouses || []);
      setStats(statRes.data.stats || {});
    } catch (err) {
      setError('Failed to load sales data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { analytics.pageView('sales'); loadData(); }, [loadData]);
  const clearMsg = () => { setError(null); setSuccess(null); };

  const handleSaveCustomer = async (data) => {
    clearMsg();
    try {
      if (editItem) { await salesAPI.updateCustomer(editItem.id, data); setSuccess('Customer updated'); }
      else { await salesAPI.createCustomer(data); setSuccess('Customer created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  const handleSaveQuotation = async (data) => {
    clearMsg();
    try {
      if (editItem) { await salesAPI.updateQuotation(editItem.id, data); setSuccess('Quotation updated'); }
      else { await salesAPI.createQuotation(data); setSuccess('Quotation created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  const handleConvert = async (quoteId) => {
    clearMsg();
    try {
      const res = await salesAPI.convertQuotation(quoteId, {});
      setSuccess(`Quotation converted to Invoice ${res.data.invoice?.number}`);
      analytics.track('quotation_converted', { quote_id: quoteId });
      loadData();
    } catch (err) { setError(err.response?.data?.error || 'Conversion failed'); }
  };

  const handleSaveInvoice = async (data) => {
    clearMsg();
    try {
      await salesAPI.createInvoice(data); setSuccess('Invoice created');
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  const handleRecordPayment = async (invId, data) => {
    clearMsg();
    try {
      await salesAPI.recordPayment(invId, data);
      setSuccess('Payment recorded');
      setPaymentModal(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Payment failed'); }
  };

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading sales...</p></div>;

  const statusBadge = (status) => {
    const cfg = STATUS_CONFIG[status] || {};
    return <span className="badge" style={{ background: cfg.bg, color: cfg.text }}>{cfg.label || status}</span>;
  };

  /* ── Table columns ── */
  const quoteCols = [
    { key: 'number', label: 'Number', sortable: true, render: (_, r) => <span className="fw-medium">{r.number}</span> },
    { key: 'customer_name', label: 'Customer', sortable: true },
    { key: 'total', label: 'Total', sortable: true, render: (v) => formatCurrency(v) },
    { key: 'status', label: 'Status', render: (v) => statusBadge(v) },
    { key: 'created_at', label: 'Date', sortable: true, render: (v) => v ? new Date(v).toLocaleDateString() : '' },
    { key: '_actions', label: 'Actions', render: (_, row) => (
      <div style={{ display: 'flex', gap: 4 }}>
        <button className="btn-icon" title="View" onClick={(e) => { e.stopPropagation(); setViewItem({ ...row, _type: 'quotation' }); }}><Eye size={15} /></button>
        {['draft', 'sent'].includes(row.status) && (
          <button className="btn-icon" title="Edit" onClick={(e) => { e.stopPropagation(); setEditItem(row); setShowForm(true); }}><Edit3 size={15} /></button>
        )}
        {['draft', 'sent', 'accepted'].includes(row.status) && (
          <button className="btn-icon" title="Convert" onClick={(e) => { e.stopPropagation(); if (window.confirm('Convert to invoice?')) handleConvert(row.id); }}><ArrowRight size={15} /></button>
        )}
      </div>
    )},
  ];
  const invoiceCols = [
    { key: 'number', label: 'Number', sortable: true, render: (_, r) => <span className="fw-medium">{r.number}</span> },
    { key: 'customer_name', label: 'Customer', sortable: true },
    { key: 'total', label: 'Total', sortable: true, render: (v) => formatCurrency(v) },
    { key: 'amount_paid', label: 'Paid', render: (v) => <span style={{ color: 'var(--success)' }}>{formatCurrency(v)}</span> },
    { key: 'balance_due', label: 'Balance', render: (v) => <span style={{ color: parseFloat(v) > 0 ? 'var(--danger)' : undefined }}>{formatCurrency(v)}</span> },
    { key: 'status', label: 'Status', render: (v) => statusBadge(v) },
    { key: '_actions', label: 'Actions', render: (_, row) => (
      <div style={{ display: 'flex', gap: 4 }}>
        <button className="btn-icon" title="View" onClick={(e) => { e.stopPropagation(); setViewItem({ ...row, _type: 'invoice' }); }}><Eye size={15} /></button>
        {['draft', 'sent', 'partial', 'overdue'].includes(row.status) && (
          <button className="btn-icon" title="Payment" onClick={(e) => { e.stopPropagation(); setPaymentModal(row); }}><DollarSign size={15} /></button>
        )}
      </div>
    )},
  ];
  const customerCols = [
    { key: 'name', label: 'Name', sortable: true, render: (_, r) => <span className="fw-medium">{r.name}</span> },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'phone', label: 'Phone' },
    { key: 'company', label: 'Company', sortable: true },
    { key: '_actions', label: 'Actions', render: (_, row) => (
      <button className="btn-icon" onClick={(e) => { e.stopPropagation(); setEditItem(row); setShowForm(true); }}><Edit3 size={15} /></button>
    )},
  ];

  const tabs = [
    { key: 'quotations', label: 'Quotations', icon: <FileText size={15} />, count: quotations.length },
    { key: 'invoices', label: 'Invoices', icon: <DollarSign size={15} />, count: invoices.length },
    { key: 'customers', label: 'Customers', icon: <Users size={15} />, count: customers.length },
  ];

  return (
    <div className="erp-page">
      <PageHeader title="Sales" subtitle="Customers, quotations, invoices & payments"
        actions={
          <button className="btn btn-primary"
            onClick={() => { setShowForm(true); setEditItem(null); setViewItem(null); }}>
            <Plus size={16} /> New {tab === 'customers' ? 'Customer' : tab === 'invoices' ? 'Invoice' : 'Quotation'}
          </button>
        }
      />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {stats && (
        <StatCards stats={[
          { label: 'Customers', value: stats.total_customers, iconColor: 'blue' },
          { label: 'Quotations', value: stats.total_quotations, iconColor: 'purple' },
          { label: 'Revenue', value: formatCurrency(stats.total_revenue || 0), iconColor: 'green' },
          { label: 'Outstanding', value: formatCurrency(stats.total_outstanding || 0), iconColor: 'orange' },
        ]} />
      )}

      <TabBar tabs={tabs} active={tab}
        onChange={(k) => { setTab(k); setShowForm(false); setEditItem(null); setViewItem(null); }} />

      {/* ── Quotations ── */}
      {tab === 'quotations' && !viewItem && (
        <div style={{ padding: '1rem 1.5rem' }}>
          {showForm && (
            <DocumentForm type="quotation" doc={editItem} customers={customers}
              products={products} warehouses={warehouses}
              onSave={handleSaveQuotation} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <DataTable columns={quoteCols} data={quotations}
            emptyTitle="No quotations yet" emptyDesc="Create your first quotation to get started" />
        </div>
      )}

      {/* ── Detail View ── */}
      {viewItem && (
        <DocumentDetail doc={viewItem} onBack={() => setViewItem(null)}
          onConvert={viewItem._type === 'quotation' ? handleConvert : undefined}
          onRecordPayment={viewItem._type === 'invoice' ? (inv) => setPaymentModal(inv) : undefined} />
      )}

      {/* ── Invoices ── */}
      {tab === 'invoices' && !viewItem && (
        <div style={{ padding: '1rem 1.5rem' }}>
          {showForm && (
            <DocumentForm type="invoice" doc={editItem} customers={customers}
              products={products} warehouses={warehouses}
              onSave={handleSaveInvoice} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <DataTable columns={invoiceCols} data={invoices}
            emptyTitle="No invoices yet" emptyDesc="Create an invoice or convert a quotation" />
        </div>
      )}

      {/* ── Customers ── */}
      {tab === 'customers' && (
        <div style={{ padding: '1rem 1.5rem' }}>
          {showForm && (
            <CustomerForm customer={editItem} onSave={handleSaveCustomer}
              onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <DataTable columns={customerCols} data={customers}
            emptyTitle="No customers yet" emptyDesc="Add your first customer" />
        </div>
      )}

      {/* ── Payment Modal ── */}
      {paymentModal && (
        <PaymentModal invoice={paymentModal} onSave={(data) => handleRecordPayment(paymentModal.id, data)}
          onClose={() => setPaymentModal(null)} />
      )}
    </div>
  );
}

/* ─── Document Form (Quotation / Invoice with line items) ─── */
function DocumentForm({ type, doc, customers, products, warehouses, onSave, onCancel }) {
  const isQuote = type === 'quotation';
  const [form, setForm] = useState({
    customer_id: doc?.customer_id || '',
    date: doc?.date || new Date().toISOString().split('T')[0],
    valid_until: doc?.valid_until || '',
    due_date: doc?.due_date || '',
    notes: doc?.notes || '',
    terms: doc?.terms || '',
    currency: doc?.currency || 'USD',
    discount_amount: doc?.discount_amount || 0,
    warehouse_id: '',
  });
  const [items, setItems] = useState(doc?.items?.length > 0
    ? doc.items.map(i => ({ ...i, key: Math.random() }))
    : [{ key: Math.random(), product_id: '', description: '', quantity: 1, unit_price: 0, discount_pct: 0, tax_rate: 0 }]
  );
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const addItem = () => setItems(i => [...i, { key: Math.random(), product_id: '', description: '', quantity: 1, unit_price: 0, discount_pct: 0, tax_rate: 0 }]);
  const removeItem = (idx) => setItems(i => i.filter((_, j) => j !== idx));
  const updateItem = (idx, field, value) => {
    setItems(prev => prev.map((item, j) => {
      if (j !== idx) return item;
      const updated = { ...item, [field]: value };
      if (field === 'product_id' && value) {
        const prod = products.find(p => String(p.id) === String(value));
        if (prod) {
          updated.description = prod.name;
          updated.unit_price = parseFloat(prod.sale_price) || 0;
          updated.tax_rate = parseFloat(prod.tax_rate) || 0;
        }
      }
      return updated;
    }));
  };

  const calcLineTotal = (item) => {
    const qty = parseFloat(item.quantity) || 0;
    const price = parseFloat(item.unit_price) || 0;
    const disc = parseFloat(item.discount_pct) || 0;
    const tax = parseFloat(item.tax_rate) || 0;
    const subtotal = qty * price * (1 - disc / 100);
    return subtotal * (1 + tax / 100);
  };
  const subtotal = items.reduce((sum, i) => sum + calcLineTotal(i), 0);
  const grandTotal = subtotal - (parseFloat(form.discount_amount) || 0);

  const handleSubmit = () => {
    onSave({
      ...form,
      items: items.map(i => ({
        product_id: i.product_id, description: i.description,
        quantity: i.quantity, unit_price: i.unit_price,
        discount_pct: i.discount_pct, tax_rate: i.tax_rate,
      })),
    });
  };

  const liColumns = [
    { key: 'product_id', label: 'Product', type: 'select', width: '28%',
      options: products.map(p => ({ value: p.id, label: `${p.name} (${p.sku || 'no SKU'})` })) },
    { key: 'description', label: 'Description', type: 'text' },
    { key: 'quantity', label: 'Qty', type: 'number', width: '8%' },
    { key: 'unit_price', label: 'Price', type: 'number', width: '10%' },
    { key: 'discount_pct', label: 'Disc %', type: 'number', width: '8%' },
    { key: 'tax_rate', label: 'Tax %', type: 'number', width: '8%' },
    { key: '_total', label: 'Total', type: 'computed', width: '10%' },
  ];

  const liRows = items.map(i => ({ ...i, _total: calcLineTotal(i) }));

  return (
    <div className="card" style={{ marginBottom: '1rem' }}>
      <div className="card-header">
        <h3>{doc ? 'Edit' : 'New'} {isQuote ? 'Quotation' : 'Invoice'}</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button>
      </div>
      <div className="card-body">
        <div className="df-grid cols-2" style={{ marginBottom: '1rem' }}>
          <div className="df-field">
            <label className="df-label">Customer <span className="required">*</span></label>
            <select className="df-select" value={form.customer_id} onChange={e => set('customer_id', e.target.value)}>
              <option value="">Select customer</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.name}{c.company ? ` (${c.company})` : ''}</option>)}
            </select>
          </div>
          <div className="df-field">
            <label className="df-label">Date</label>
            <input className="df-input" type="date" value={form.date} onChange={e => set('date', e.target.value)} />
          </div>
          {isQuote && <div className="df-field"><label className="df-label">Valid Until</label><input className="df-input" type="date" value={form.valid_until} onChange={e => set('valid_until', e.target.value)} /></div>}
          {!isQuote && <div className="df-field"><label className="df-label">Due Date</label><input className="df-input" type="date" value={form.due_date} onChange={e => set('due_date', e.target.value)} /></div>}
          {!isQuote && warehouses.length > 0 && (
            <div className="df-field"><label className="df-label">Warehouse</label>
              <select className="df-select" value={form.warehouse_id} onChange={e => set('warehouse_id', e.target.value)}>
                <option value="">No stock deduction</option>
                {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select></div>
          )}
        </div>

        <LineItems
          columns={liColumns}
          rows={liRows}
          onChange={(idx, field, val) => updateItem(idx, field, val)}
          onAdd={addItem}
          onRemove={removeItem}
          totals={[
            { label: 'Subtotal', value: subtotal },
            { label: 'Discount', value: parseFloat(form.discount_amount) || 0 },
            { label: 'Total', value: grandTotal, grand: true },
          ]}
        />

        <div className="df-grid cols-2" style={{ marginTop: '1rem' }}>
          <div className="df-field full"><label className="df-label">Notes</label><textarea className="df-textarea" value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} /></div>
        </div>
      </div>
      <div className="modal-dialog-footer">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={handleSubmit} disabled={!form.customer_id || items.length === 0}>
          Save {isQuote ? 'Quotation' : 'Invoice'}
        </button>
      </div>
    </div>
  );
}

/* ─── Document Detail View ─── */
function DocumentDetail({ doc, onBack, onConvert, onRecordPayment }) {
  const isQuote = doc._type === 'quotation';
  return (
    <div className="card" style={{ margin: '1rem 1.5rem' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
          <button className="btn btn-secondary" onClick={onBack}>&larr; Back</button>
          <h3>{doc.number}</h3>
          {(() => { const cfg = STATUS_CONFIG[doc.status] || {}; return <span className="badge" style={{ background: cfg.bg, color: cfg.text }}>{cfg.label || doc.status}</span>; })()}
        </div>
        <div style={{ display: 'flex', gap: '.5rem' }}>
          {isQuote && ['draft', 'sent', 'accepted'].includes(doc.status) && (
            <button className="btn btn-success" onClick={() => { if (window.confirm('Convert to invoice?')) onConvert(doc.id); }}>
              <ArrowRight size={16} /> Convert
            </button>
          )}
          {!isQuote && ['draft', 'sent', 'partial', 'overdue'].includes(doc.status) && onRecordPayment && (
            <button className="btn btn-success" onClick={() => onRecordPayment(doc)}>
              <DollarSign size={16} /> Record Payment
            </button>
          )}
        </div>
      </div>
      <div className="card-body">
        <div className="df-grid cols-3" style={{ marginBottom: '1rem' }}>
          <div className="df-field"><label className="df-label">Customer</label><div>{doc.customer_name || '-'}</div></div>
          <div className="df-field"><label className="df-label">Date</label><div>{doc.date}</div></div>
          {isQuote && <div className="df-field"><label className="df-label">Valid Until</label><div>{doc.valid_until || '-'}</div></div>}
          {!isQuote && <div className="df-field"><label className="df-label">Due Date</label><div>{doc.due_date || '-'}</div></div>}
          {!isQuote && <div className="df-field"><label className="df-label">Paid</label><div style={{ color: 'var(--success)' }}>{formatCurrency(doc.amount_paid)}</div></div>}
          {!isQuote && <div className="df-field"><label className="df-label">Balance</label><div style={{ color: parseFloat(doc.balance_due) > 0 ? 'var(--danger)' : undefined }}>{formatCurrency(doc.balance_due)}</div></div>}
        </div>
        {doc.items?.length > 0 && (
          <div className="li-table-wrap">
            <table className="li-table">
              <thead><tr><th>#</th><th>Product</th><th>Description</th><th>Qty</th><th>Price</th><th>Disc %</th><th>Tax %</th><th className="text-right">Total</th></tr></thead>
              <tbody>
                {doc.items.map((item, idx) => (
                  <tr key={item.id || idx}>
                    <td>{idx + 1}</td>
                    <td>{item.product_name || '-'}</td>
                    <td>{item.description}</td>
                    <td>{item.quantity}</td>
                    <td>{formatCurrency(item.unit_price)}</td>
                    <td>{item.discount_pct}%</td>
                    <td>{item.tax_rate}%</td>
                    <td className="text-right">{formatCurrency(item.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="li-totals">
          <table><tbody>
            <tr><td className="label">Subtotal:</td><td className="value">{formatCurrency(doc.subtotal)}</td></tr>
            <tr><td className="label">Tax:</td><td className="value">{formatCurrency(doc.tax_amount)}</td></tr>
            {parseFloat(doc.discount_amount) > 0 && <tr><td className="label">Discount:</td><td className="value">-{formatCurrency(doc.discount_amount)}</td></tr>}
            <tr className="grand"><td className="label">Total:</td><td className="value">{formatCurrency(doc.total)}</td></tr>
          </tbody></table>
        </div>
        {doc.notes && <div style={{ marginTop: '1rem' }}><strong>Notes:</strong> {doc.notes}</div>}
      </div>
    </div>
  );
}

/* ─── Customer Form ─── */
function CustomerForm({ customer, onSave, onCancel }) {
  const [form, setForm] = useState({
    name: customer?.name || '', email: customer?.email || '',
    phone: customer?.phone || '', company: customer?.company || '',
    address: customer?.address || '', tax_id: customer?.tax_id || '',
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  return (
    <div className="card" style={{ marginBottom: '1rem' }}>
      <div className="card-header"><h3>{customer ? 'Edit' : 'New'} Customer</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button></div>
      <div className="card-body">
        <div className="df-grid cols-2">
          <div className="df-field"><label className="df-label">Name <span className="required">*</span></label><input className="df-input" value={form.name} onChange={e => set('name', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Email</label><input className="df-input" type="email" value={form.email} onChange={e => set('email', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Phone</label><input className="df-input" value={form.phone} onChange={e => set('phone', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Company</label><input className="df-input" value={form.company} onChange={e => set('company', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Tax ID</label><input className="df-input" value={form.tax_id} onChange={e => set('tax_id', e.target.value)} /></div>
          <div className="df-field full"><label className="df-label">Address</label><textarea className="df-textarea" value={form.address} onChange={e => set('address', e.target.value)} rows={2} /></div>
        </div>
      </div>
      <div className="modal-dialog-footer">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)} disabled={!form.name}>Save</button>
      </div>
    </div>
  );
}

/* ─── Payment Modal ─── */
function PaymentModal({ invoice, onSave, onClose }) {
  const [form, setForm] = useState({ amount: '', payment_method: 'bank_transfer', reference: '', notes: '', date: new Date().toISOString().split('T')[0] });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const balance = parseFloat(invoice.balance_due || 0);
  return (
    <Modal title={`Record Payment — ${invoice.number}`} onClose={onClose} size="md"
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-success" onClick={() => onSave(form)} disabled={!form.amount || parseFloat(form.amount) <= 0}>
            <DollarSign size={16} /> Record Payment
          </button>
        </>
      }
    >
      <p style={{ marginBottom: '1rem' }}>Balance due: <strong style={{ color: 'var(--danger)' }}>{formatCurrency(balance)}</strong></p>
      <div className="df-grid cols-2">
        <div className="df-field"><label className="df-label">Amount <span className="required">*</span></label>
          <input className="df-input" type="number" step="0.01" max={balance} value={form.amount} onChange={e => set('amount', e.target.value)} /></div>
        <div className="df-field"><label className="df-label">Method</label>
          <select className="df-select" value={form.payment_method} onChange={e => set('payment_method', e.target.value)}>
            {PAYMENT_METHODS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select></div>
        <div className="df-field"><label className="df-label">Date</label><input className="df-input" type="date" value={form.date} onChange={e => set('date', e.target.value)} /></div>
        <div className="df-field"><label className="df-label">Reference</label><input className="df-input" value={form.reference} onChange={e => set('reference', e.target.value)} /></div>
        <div className="df-field full"><label className="df-label">Notes</label><textarea className="df-textarea" value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} /></div>
      </div>
    </Modal>
  );
}

export default SalesPage;
