import React, { useState, useEffect, useCallback } from 'react';
import { salesAPI, inventoryAPI } from '../services/api';
import analytics from '../services/analytics';
import {
  ShoppingCart, Plus, Search, Edit3, Eye, FileText, DollarSign,
  Users, ArrowRight, AlertCircle, Check, X, RefreshCw,
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

  /* ── Customer CRUD ── */
  const handleSaveCustomer = async (data) => {
    clearMsg();
    try {
      if (editItem) { await salesAPI.updateCustomer(editItem.id, data); setSuccess('Customer updated'); }
      else { await salesAPI.createCustomer(data); setSuccess('Customer created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  /* ── Quotation CRUD ── */
  const handleSaveQuotation = async (data) => {
    clearMsg();
    try {
      if (editItem) { await salesAPI.updateQuotation(editItem.id, data); setSuccess('Quotation updated'); }
      else { await salesAPI.createQuotation(data); setSuccess('Quotation created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  /* ── Convert Quotation → Invoice ── */
  const handleConvert = async (quoteId) => {
    clearMsg();
    try {
      const res = await salesAPI.convertQuotation(quoteId, {});
      setSuccess(`Quotation converted to Invoice ${res.data.invoice?.number}`);
      analytics.track('quotation_converted', { quote_id: quoteId });
      loadData();
    } catch (err) { setError(err.response?.data?.error || 'Conversion failed'); }
  };

  /* ── Invoice CRUD ── */
  const handleSaveInvoice = async (data) => {
    clearMsg();
    try {
      await salesAPI.createInvoice(data); setSuccess('Invoice created');
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  /* ── Payment ── */
  const handleRecordPayment = async (invId, data) => {
    clearMsg();
    try {
      await salesAPI.recordPayment(invId, data);
      setSuccess('Payment recorded');
      setPaymentModal(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Payment failed'); }
  };

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading sales...</p></div>;

  return (
    <div className="erp-page">
      <header className="page-header">
        <div>
          <h1><ShoppingCart size={24} /> Sales</h1>
          <p className="header-subtitle">Customers, quotations, invoices & payments</p>
        </div>
      </header>

      {error && <div className="alert alert-danger"><AlertCircle size={16} /> {error} <button className="alert-close" onClick={() => setError(null)}>&times;</button></div>}
      {success && <div className="alert alert-success"><Check size={16} /> {success} <button className="alert-close" onClick={() => setSuccess(null)}>&times;</button></div>}

      {stats && (
        <div className="stat-grid sm">
          <div className="stat-card stat-blue"><div className="stat-card-header"><span className="stat-card-label">Customers</span></div><div className="stat-card-value">{stats.total_customers}</div></div>
          <div className="stat-card stat-purple"><div className="stat-card-header"><span className="stat-card-label">Quotations</span></div><div className="stat-card-value">{stats.total_quotations}</div></div>
          <div className="stat-card stat-green"><div className="stat-card-header"><span className="stat-card-label">Revenue</span></div><div className="stat-card-value">${(stats.total_revenue || 0).toLocaleString()}</div></div>
          <div className="stat-card stat-orange"><div className="stat-card-header"><span className="stat-card-label">Outstanding</span></div><div className="stat-card-value">${(stats.total_outstanding || 0).toLocaleString()}</div></div>
        </div>
      )}

      <div className="erp-tabs">
        {[
          { key: 'quotations', label: 'Quotations', icon: FileText },
          { key: 'invoices', label: 'Invoices', icon: DollarSign },
          { key: 'customers', label: 'Customers', icon: Users },
        ].map(t => (
          <button key={t.key} className={`erp-tab ${tab === t.key ? 'active' : ''}`}
            onClick={() => { setTab(t.key); setShowForm(false); setEditItem(null); setViewItem(null); }}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* ── Quotations Tab ── */}
      {tab === 'quotations' && !viewItem && (
        <div className="erp-section">
          <div className="section-toolbar">
            <span />
            <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditItem(null); }}>
              <Plus size={16} /> New Quotation
            </button>
          </div>
          {showForm && (
            <DocumentForm type="quotation" doc={editItem} customers={customers}
              products={products} warehouses={warehouses}
              onSave={handleSaveQuotation} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Number</th><th>Customer</th><th>Date</th><th>Total</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {quotations.map(q => (
                  <tr key={q.id}>
                    <td className="fw-medium">{q.number}</td>
                    <td>{q.customer_name || '-'}</td>
                    <td>{q.date}</td>
                    <td>${parseFloat(q.total || 0).toFixed(2)}</td>
                    <td><span className={`badge status-${q.status}`}>{q.status}</span></td>
                    <td className="actions-cell">
                      <button className="btn-icon" title="View" onClick={() => setViewItem({ ...q, _type: 'quotation' })}><Eye size={15} /></button>
                      {['draft', 'sent'].includes(q.status) && (
                        <button className="btn-icon" title="Edit" onClick={() => { setEditItem(q); setShowForm(true); }}><Edit3 size={15} /></button>
                      )}
                      {['draft', 'sent', 'accepted'].includes(q.status) && (
                        <button className="btn-icon" title="Convert to Invoice"
                          onClick={() => { if (window.confirm('Convert this quotation to an invoice?')) handleConvert(q.id); }}>
                          <ArrowRight size={15} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {quotations.length === 0 && <tr><td colSpan={6} className="empty-row">No quotations</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Quotation / Invoice Detail View ── */}
      {viewItem && (
        <DocumentDetail doc={viewItem} onBack={() => setViewItem(null)}
          onConvert={viewItem._type === 'quotation' ? handleConvert : undefined}
          onRecordPayment={viewItem._type === 'invoice' ? (inv) => setPaymentModal(inv) : undefined} />
      )}

      {/* ── Invoices Tab ── */}
      {tab === 'invoices' && !viewItem && (
        <div className="erp-section">
          <div className="section-toolbar">
            <span />
            <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditItem(null); }}>
              <Plus size={16} /> New Invoice
            </button>
          </div>
          {showForm && (
            <DocumentForm type="invoice" doc={editItem} customers={customers}
              products={products} warehouses={warehouses}
              onSave={handleSaveInvoice} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Number</th><th>Customer</th><th>Date</th><th>Total</th><th>Paid</th><th>Balance</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {invoices.map(inv => (
                  <tr key={inv.id}>
                    <td className="fw-medium">{inv.number}</td>
                    <td>{inv.customer_name || '-'}</td>
                    <td>{inv.date}</td>
                    <td>${parseFloat(inv.total || 0).toFixed(2)}</td>
                    <td className="text-success">${parseFloat(inv.amount_paid || 0).toFixed(2)}</td>
                    <td className={parseFloat(inv.balance_due || 0) > 0 ? 'text-danger' : ''}>${parseFloat(inv.balance_due || 0).toFixed(2)}</td>
                    <td><span className={`badge status-${inv.status}`}>{inv.status}</span></td>
                    <td className="actions-cell">
                      <button className="btn-icon" title="View" onClick={() => setViewItem({ ...inv, _type: 'invoice' })}><Eye size={15} /></button>
                      {['draft', 'sent', 'partial', 'overdue'].includes(inv.status) && (
                        <button className="btn-icon" title="Record Payment" onClick={() => setPaymentModal(inv)}><DollarSign size={15} /></button>
                      )}
                    </td>
                  </tr>
                ))}
                {invoices.length === 0 && <tr><td colSpan={8} className="empty-row">No invoices</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Customers Tab ── */}
      {tab === 'customers' && (
        <div className="erp-section">
          <div className="section-toolbar">
            <span />
            <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditItem(null); }}>
              <Plus size={16} /> Add Customer
            </button>
          </div>
          {showForm && (
            <CustomerForm customer={editItem} onSave={handleSaveCustomer}
              onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Company</th><th>Actions</th></tr></thead>
              <tbody>
                {customers.map(c => (
                  <tr key={c.id}>
                    <td className="fw-medium">{c.name}</td>
                    <td>{c.email || '-'}</td>
                    <td>{c.phone || '-'}</td>
                    <td>{c.company || '-'}</td>
                    <td className="actions-cell">
                      <button className="btn-icon" onClick={() => { setEditItem(c); setShowForm(true); }}><Edit3 size={15} /></button>
                    </td>
                  </tr>
                ))}
                {customers.length === 0 && <tr><td colSpan={5} className="empty-row">No customers</td></tr>}
              </tbody>
            </table>
          </div>
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

/* ─── Document Form (Quotation / Invoice with line items + product picker) ─── */
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
  const removeItem = (key) => setItems(i => i.filter(x => x.key !== key));
  const updateItem = (key, field, value) => {
    setItems(prev => prev.map(item => {
      if (item.key !== key) return item;
      const updated = { ...item, [field]: value };
      // Auto-fill from product
      if (field === 'product_id' && value) {
        const prod = products.find(p => p.id === value);
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
  const grandTotal = items.reduce((sum, i) => sum + calcLineTotal(i), 0) - (parseFloat(form.discount_amount) || 0);

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

  return (
    <div className="document-section">
      <div className="document-header">
        <h3>{doc ? 'Edit' : 'New'} {isQuote ? 'Quotation' : 'Invoice'}</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button>
      </div>
      <div className="document-body">
        <div className="form-grid">
          <div className="form-group"><label>Customer *</label>
            <select value={form.customer_id} onChange={e => set('customer_id', e.target.value)}>
              <option value="">Select customer</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.name}{c.company ? ` (${c.company})` : ''}</option>)}
            </select></div>
          <div className="form-group"><label>Date</label><input type="date" value={form.date} onChange={e => set('date', e.target.value)} /></div>
          {isQuote && <div className="form-group"><label>Valid Until</label><input type="date" value={form.valid_until} onChange={e => set('valid_until', e.target.value)} /></div>}
          {!isQuote && <div className="form-group"><label>Due Date</label><input type="date" value={form.due_date} onChange={e => set('due_date', e.target.value)} /></div>}
          {!isQuote && warehouses.length > 0 && (
            <div className="form-group"><label>Warehouse (for stock)</label>
              <select value={form.warehouse_id} onChange={e => set('warehouse_id', e.target.value)}>
                <option value="">No stock deduction</option>
                {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select></div>
          )}
        </div>

        <h4 style={{ margin: '1rem 0 .5rem' }}>Line Items</h4>
        <table className="line-items-table">
          <thead><tr><th style={{width:'30%'}}>Product</th><th>Description</th><th style={{width:'8%'}}>Qty</th><th style={{width:'10%'}}>Price</th><th style={{width:'8%'}}>Disc %</th><th style={{width:'8%'}}>Tax %</th><th style={{width:'10%'}}>Total</th><th style={{width:'3%'}}></th></tr></thead>
          <tbody>
            {items.map(item => (
              <tr key={item.key}>
                <td>
                  <select value={item.product_id} onChange={e => updateItem(item.key, 'product_id', e.target.value)}>
                    <option value="">Select product</option>
                    {products.map(p => <option key={p.id} value={p.id}>{p.name} ({p.sku || 'no SKU'})</option>)}
                  </select>
                </td>
                <td><input value={item.description} onChange={e => updateItem(item.key, 'description', e.target.value)} /></td>
                <td><input type="number" min="1" value={item.quantity} onChange={e => updateItem(item.key, 'quantity', e.target.value)} /></td>
                <td><input type="number" step="0.01" value={item.unit_price} onChange={e => updateItem(item.key, 'unit_price', e.target.value)} /></td>
                <td><input type="number" step="0.01" value={item.discount_pct} onChange={e => updateItem(item.key, 'discount_pct', e.target.value)} /></td>
                <td><input type="number" step="0.01" value={item.tax_rate} onChange={e => updateItem(item.key, 'tax_rate', e.target.value)} /></td>
                <td style={{textAlign:'right', fontWeight:500}}>${calcLineTotal(item).toFixed(2)}</td>
                <td><button className="remove-row" onClick={() => removeItem(item.key)}><X size={14} /></button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <button className="btn btn-secondary" style={{marginTop:'.5rem'}} onClick={addItem}><Plus size={14} /> Add Line</button>

        <div className="document-totals">
          <table className="totals-table">
            <tbody>
              <tr><td className="total-label">Discount:</td><td className="total-value">
                <input type="number" step="0.01" style={{width:100,textAlign:'right'}}
                  value={form.discount_amount} onChange={e => set('discount_amount', e.target.value)} />
              </td></tr>
              <tr className="grand-total"><td className="total-label">Total:</td><td className="total-value">${grandTotal.toFixed(2)}</td></tr>
            </tbody>
          </table>
        </div>

        <div className="form-grid" style={{marginTop:'.75rem'}}>
          <div className="form-group full"><label>Notes</label><textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} /></div>
          <div className="form-group full"><label>Terms</label><textarea value={form.terms} onChange={e => set('terms', e.target.value)} rows={2} /></div>
        </div>
      </div>
      <div className="card-footer">
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
    <div className="document-section">
      <div className="document-header">
        <div style={{display:'flex',alignItems:'center',gap:'.75rem'}}>
          <button className="btn btn-secondary" onClick={onBack}>&larr; Back</button>
          <h3>{doc.number}</h3>
          <span className={`badge status-${doc.status}`}>{doc.status}</span>
        </div>
        <div style={{display:'flex',gap:'.5rem'}}>
          {isQuote && ['draft', 'sent', 'accepted'].includes(doc.status) && (
            <button className="btn btn-success" onClick={() => { if (window.confirm('Convert to invoice?')) onConvert(doc.id); }}>
              <ArrowRight size={16} /> Convert to Invoice
            </button>
          )}
          {!isQuote && ['draft','sent','partial','overdue'].includes(doc.status) && onRecordPayment && (
            <button className="btn btn-success" onClick={() => onRecordPayment(doc)}>
              <DollarSign size={16} /> Record Payment
            </button>
          )}
        </div>
      </div>
      <div className="document-body">
        <div className="form-grid">
          <div className="form-group"><label>Customer</label><div>{doc.customer_name || '-'}</div></div>
          <div className="form-group"><label>Date</label><div>{doc.date}</div></div>
          {isQuote && <div className="form-group"><label>Valid Until</label><div>{doc.valid_until || '-'}</div></div>}
          {!isQuote && <div className="form-group"><label>Due Date</label><div>{doc.due_date || '-'}</div></div>}
          {!isQuote && <div className="form-group"><label>Amount Paid</label><div className="text-success">${parseFloat(doc.amount_paid || 0).toFixed(2)}</div></div>}
          {!isQuote && <div className="form-group"><label>Balance Due</label><div className={parseFloat(doc.balance_due) > 0 ? 'text-danger' : ''}>${parseFloat(doc.balance_due || 0).toFixed(2)}</div></div>}
        </div>
        {doc.items?.length > 0 && (
          <>
            <h4 style={{margin:'1rem 0 .5rem'}}>Items</h4>
            <div className="data-table-wrap">
              <table className="data-table">
                <thead><tr><th>#</th><th>Product</th><th>Description</th><th>Qty</th><th>Price</th><th>Disc %</th><th>Tax %</th><th>Total</th></tr></thead>
                <tbody>
                  {doc.items.map((item, idx) => (
                    <tr key={item.id || idx}>
                      <td>{idx + 1}</td>
                      <td>{item.product_name || '-'}</td>
                      <td>{item.description}</td>
                      <td>{item.quantity}</td>
                      <td>${parseFloat(item.unit_price).toFixed(2)}</td>
                      <td>{item.discount_pct}%</td>
                      <td>{item.tax_rate}%</td>
                      <td>${parseFloat(item.total || 0).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <div className="document-totals">
          <table className="totals-table"><tbody>
            <tr><td className="total-label">Subtotal:</td><td className="total-value">${parseFloat(doc.subtotal || 0).toFixed(2)}</td></tr>
            <tr><td className="total-label">Tax:</td><td className="total-value">${parseFloat(doc.tax_amount || 0).toFixed(2)}</td></tr>
            {parseFloat(doc.discount_amount) > 0 && <tr><td className="total-label">Discount:</td><td className="total-value">-${parseFloat(doc.discount_amount).toFixed(2)}</td></tr>}
            <tr className="grand-total"><td className="total-label">Total:</td><td className="total-value">${parseFloat(doc.total || 0).toFixed(2)}</td></tr>
          </tbody></table>
        </div>
        {doc.notes && <div style={{marginTop:'1rem'}}><strong>Notes:</strong> {doc.notes}</div>}
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
    <div className="erp-form card">
      <div className="card-header"><h3>{customer ? 'Edit' : 'New'} Customer</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button></div>
      <div className="card-body form-grid">
        <div className="form-group"><label>Name *</label><input value={form.name} onChange={e => set('name', e.target.value)} /></div>
        <div className="form-group"><label>Email</label><input type="email" value={form.email} onChange={e => set('email', e.target.value)} /></div>
        <div className="form-group"><label>Phone</label><input value={form.phone} onChange={e => set('phone', e.target.value)} /></div>
        <div className="form-group"><label>Company</label><input value={form.company} onChange={e => set('company', e.target.value)} /></div>
        <div className="form-group"><label>Tax ID</label><input value={form.tax_id} onChange={e => set('tax_id', e.target.value)} /></div>
        <div className="form-group full"><label>Address</label><textarea value={form.address} onChange={e => set('address', e.target.value)} rows={2} /></div>
      </div>
      <div className="card-footer">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)}>Save</button>
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
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Record Payment — {invoice.number}</h3>
          <button className="btn-icon" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          <p style={{marginBottom:'1rem'}}>Balance due: <strong className="text-danger">${balance.toFixed(2)}</strong></p>
          <div className="form-grid">
            <div className="form-group"><label>Amount *</label>
              <input type="number" step="0.01" max={balance} value={form.amount} onChange={e => set('amount', e.target.value)} /></div>
            <div className="form-group"><label>Method</label>
              <select value={form.payment_method} onChange={e => set('payment_method', e.target.value)}>
                <option value="bank_transfer">Bank Transfer</option><option value="cash">Cash</option>
                <option value="credit_card">Credit Card</option><option value="cheque">Cheque</option>
                <option value="other">Other</option>
              </select></div>
            <div className="form-group"><label>Date</label><input type="date" value={form.date} onChange={e => set('date', e.target.value)} /></div>
            <div className="form-group"><label>Reference</label><input value={form.reference} onChange={e => set('reference', e.target.value)} /></div>
            <div className="form-group full"><label>Notes</label><textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} /></div>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-success" onClick={() => onSave(form)} disabled={!form.amount || parseFloat(form.amount) <= 0}>
            <DollarSign size={16} /> Record Payment
          </button>
        </div>
      </div>
    </div>
  );
}

export default SalesPage;
