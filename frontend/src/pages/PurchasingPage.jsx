import React, { useState, useEffect, useCallback } from 'react';
import { purchasingAPI, inventoryAPI } from '../services/api';
import analytics from '../services/analytics';
import {
  Truck, Plus, Edit3, Eye, Package, Users,
  AlertCircle, Check, X, CheckCircle,
} from 'lucide-react';
import '../styles/erp.css';

function PurchasingPage() {
  const [tab, setTab] = useState('orders');
  const [suppliers, setSuppliers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [viewItem, setViewItem] = useState(null);
  const [receiveModal, setReceiveModal] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [supRes, ordRes, prodRes, whRes, statRes] = await Promise.all([
        purchasingAPI.listSuppliers({}).catch(() => ({ data: { suppliers: [] } })),
        purchasingAPI.listOrders({}).catch(() => ({ data: { orders: [] } })),
        inventoryAPI.listProducts({}).catch(() => ({ data: { products: [] } })),
        inventoryAPI.listWarehouses().catch(() => ({ data: { warehouses: [] } })),
        purchasingAPI.stats().catch(() => ({ data: { stats: {} } })),
      ]);
      setSuppliers(supRes.data.suppliers || []);
      setOrders(ordRes.data.orders || []);
      setProducts(prodRes.data.products || []);
      setWarehouses(whRes.data.warehouses || []);
      setStats(statRes.data.stats || {});
    } catch (err) { setError('Failed to load purchasing data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { analytics.pageView('purchasing'); loadData(); }, [loadData]);
  const clearMsg = () => { setError(null); setSuccess(null); };

  /* ── Supplier CRUD ── */
  const handleSaveSupplier = async (data) => {
    clearMsg();
    try {
      if (editItem) { await purchasingAPI.updateSupplier(editItem.id, data); setSuccess('Supplier updated'); }
      else { await purchasingAPI.createSupplier(data); setSuccess('Supplier created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  /* ── PO CRUD ── */
  const handleSaveOrder = async (data) => {
    clearMsg();
    try {
      if (editItem) { await purchasingAPI.updateOrder(editItem.id, data); setSuccess('Order updated'); }
      else { await purchasingAPI.createOrder(data); setSuccess('Purchase order created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  /* ── Receive Goods ── */
  const handleReceiveGoods = async (poId, items) => {
    clearMsg();
    try {
      await purchasingAPI.receiveGoods(poId, { items });
      setSuccess('Goods received — stock updated');
      setReceiveModal(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Receive failed'); }
  };

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading purchasing...</p></div>;

  return (
    <div className="erp-page">
      <header className="page-header">
        <div>
          <h1><Truck size={24} /> Purchasing</h1>
          <p className="header-subtitle">Suppliers, purchase orders & goods receipt</p>
        </div>
      </header>

      {error && <div className="alert alert-danger"><AlertCircle size={16} /> {error} <button className="alert-close" onClick={() => setError(null)}>&times;</button></div>}
      {success && <div className="alert alert-success"><Check size={16} /> {success} <button className="alert-close" onClick={() => setSuccess(null)}>&times;</button></div>}

      {stats && (
        <div className="stat-grid sm">
          <div className="stat-card stat-blue"><div className="stat-card-header"><span className="stat-card-label">Suppliers</span></div><div className="stat-card-value">{stats.total_suppliers}</div></div>
          <div className="stat-card stat-purple"><div className="stat-card-header"><span className="stat-card-label">Orders</span></div><div className="stat-card-value">{stats.total_orders}</div></div>
          <div className="stat-card stat-green"><div className="stat-card-header"><span className="stat-card-label">Total Value</span></div><div className="stat-card-value">${(stats.total_value || 0).toLocaleString()}</div></div>
          <div className="stat-card stat-orange"><div className="stat-card-header"><span className="stat-card-label">Pending</span></div><div className="stat-card-value">{stats.pending_orders}</div></div>
        </div>
      )}

      <div className="erp-tabs">
        {[
          { key: 'orders', label: 'Purchase Orders', icon: Package },
          { key: 'suppliers', label: 'Suppliers', icon: Users },
        ].map(t => (
          <button key={t.key} className={`erp-tab ${tab === t.key ? 'active' : ''}`}
            onClick={() => { setTab(t.key); setShowForm(false); setEditItem(null); setViewItem(null); }}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* ── Purchase Orders Tab ── */}
      {tab === 'orders' && !viewItem && (
        <div className="erp-section">
          <div className="section-toolbar">
            <span />
            <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditItem(null); }}>
              <Plus size={16} /> New Purchase Order
            </button>
          </div>
          {showForm && (
            <POForm po={editItem} suppliers={suppliers} products={products}
              warehouses={warehouses}
              onSave={handleSaveOrder} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Number</th><th>Supplier</th><th>Date</th><th>Total</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.id}>
                    <td className="fw-medium">{o.number}</td>
                    <td>{o.supplier_name || '-'}</td>
                    <td>{o.date}</td>
                    <td>${parseFloat(o.total || 0).toFixed(2)}</td>
                    <td><span className={`badge status-${o.status}`}>{o.status}</span></td>
                    <td className="actions-cell">
                      <button className="btn-icon" title="View" onClick={() => setViewItem(o)}><Eye size={15} /></button>
                      {['draft','sent'].includes(o.status) && (
                        <button className="btn-icon" title="Edit" onClick={() => { setEditItem(o); setShowForm(true); }}><Edit3 size={15} /></button>
                      )}
                      {['sent','partial'].includes(o.status) && (
                        <button className="btn-icon" title="Receive Goods" onClick={() => setReceiveModal(o)}><CheckCircle size={15} /></button>
                      )}
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && <tr><td colSpan={6} className="empty-row">No purchase orders</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── PO Detail ── */}
      {viewItem && (
        <div className="document-section">
          <div className="document-header">
            <div style={{display:'flex',alignItems:'center',gap:'.75rem'}}>
              <button className="btn btn-secondary" onClick={() => setViewItem(null)}>&larr; Back</button>
              <h3>{viewItem.number}</h3>
              <span className={`badge status-${viewItem.status}`}>{viewItem.status}</span>
            </div>
            {['sent','partial'].includes(viewItem.status) && (
              <button className="btn btn-success" onClick={() => setReceiveModal(viewItem)}>
                <CheckCircle size={16} /> Receive Goods
              </button>
            )}
          </div>
          <div className="document-body">
            <div className="form-grid">
              <div className="form-group"><label>Supplier</label><div>{viewItem.supplier_name || '-'}</div></div>
              <div className="form-group"><label>Date</label><div>{viewItem.date}</div></div>
              <div className="form-group"><label>Expected</label><div>{viewItem.expected_date || '-'}</div></div>
              <div className="form-group"><label>Warehouse</label><div>{viewItem.warehouse_name || '-'}</div></div>
            </div>
            {viewItem.items?.length > 0 && (
              <div className="data-table-wrap" style={{marginTop:'1rem'}}>
                <table className="data-table">
                  <thead><tr><th>#</th><th>Product</th><th>Ordered</th><th>Received</th><th>Price</th><th>Total</th></tr></thead>
                  <tbody>
                    {viewItem.items.map((item, idx) => (
                      <tr key={item.id || idx}>
                        <td>{idx+1}</td>
                        <td>{item.product_name || item.description}</td>
                        <td>{item.quantity}</td>
                        <td className={parseFloat(item.received_qty) >= parseFloat(item.quantity) ? 'text-success' : ''}>{item.received_qty || 0}</td>
                        <td>${parseFloat(item.unit_price).toFixed(2)}</td>
                        <td>${parseFloat(item.total || 0).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="document-totals">
              <table className="totals-table"><tbody>
                <tr className="grand-total"><td className="total-label">Total:</td><td className="total-value">${parseFloat(viewItem.total || 0).toFixed(2)}</td></tr>
              </tbody></table>
            </div>
          </div>
        </div>
      )}

      {/* ── Suppliers Tab ── */}
      {tab === 'suppliers' && (
        <div className="erp-section">
          <div className="section-toolbar">
            <span />
            <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditItem(null); }}>
              <Plus size={16} /> Add Supplier
            </button>
          </div>
          {showForm && (
            <SupplierForm supplier={editItem} onSave={handleSaveSupplier}
              onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Company</th><th>Actions</th></tr></thead>
              <tbody>
                {suppliers.map(s => (
                  <tr key={s.id}>
                    <td className="fw-medium">{s.name}</td>
                    <td>{s.email || '-'}</td>
                    <td>{s.phone || '-'}</td>
                    <td>{s.company || '-'}</td>
                    <td className="actions-cell">
                      <button className="btn-icon" onClick={() => { setEditItem(s); setShowForm(true); }}><Edit3 size={15} /></button>
                    </td>
                  </tr>
                ))}
                {suppliers.length === 0 && <tr><td colSpan={5} className="empty-row">No suppliers</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Receive Goods Modal ── */}
      {receiveModal && (
        <ReceiveModal po={receiveModal}
          onReceive={(items) => handleReceiveGoods(receiveModal.id, items)}
          onClose={() => setReceiveModal(null)} />
      )}
    </div>
  );
}

/* ─── PO Form ─── */
function POForm({ po, suppliers, products, warehouses, onSave, onCancel }) {
  const [form, setForm] = useState({
    supplier_id: po?.supplier_id || '', warehouse_id: po?.warehouse_id || '',
    date: po?.date || new Date().toISOString().split('T')[0],
    expected_date: po?.expected_date || '',
    notes: po?.notes || '', terms: po?.terms || '',
    currency: po?.currency || 'USD', discount_amount: po?.discount_amount || 0,
  });
  const [items, setItems] = useState(po?.items?.length > 0
    ? po.items.map(i => ({ ...i, key: Math.random() }))
    : [{ key: Math.random(), product_id: '', description: '', quantity: 1, unit_price: 0, discount_pct: 0, tax_rate: 0 }]
  );
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const addItem = () => setItems(i => [...i, { key: Math.random(), product_id: '', description: '', quantity: 1, unit_price: 0, discount_pct: 0, tax_rate: 0 }]);
  const removeItem = (key) => setItems(i => i.filter(x => x.key !== key));
  const updateItem = (key, field, value) => {
    setItems(prev => prev.map(item => {
      if (item.key !== key) return item;
      const updated = { ...item, [field]: value };
      if (field === 'product_id' && value) {
        const prod = products.find(p => p.id === value);
        if (prod) { updated.description = prod.name; updated.unit_price = parseFloat(prod.cost_price) || 0; updated.tax_rate = parseFloat(prod.tax_rate) || 0; }
      }
      return updated;
    }));
  };
  const calcLineTotal = (item) => {
    const qty = parseFloat(item.quantity) || 0;
    const price = parseFloat(item.unit_price) || 0;
    const disc = parseFloat(item.discount_pct) || 0;
    const tax = parseFloat(item.tax_rate) || 0;
    return qty * price * (1 - disc / 100) * (1 + tax / 100);
  };
  const grandTotal = items.reduce((sum, i) => sum + calcLineTotal(i), 0) - (parseFloat(form.discount_amount) || 0);

  return (
    <div className="document-section">
      <div className="document-header">
        <h3>{po ? 'Edit' : 'New'} Purchase Order</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button>
      </div>
      <div className="document-body">
        <div className="form-grid">
          <div className="form-group"><label>Supplier *</label>
            <select value={form.supplier_id} onChange={e => set('supplier_id', e.target.value)}>
              <option value="">Select supplier</option>
              {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}{s.company ? ` (${s.company})` : ''}</option>)}
            </select></div>
          <div className="form-group"><label>Warehouse *</label>
            <select value={form.warehouse_id} onChange={e => set('warehouse_id', e.target.value)}>
              <option value="">Select warehouse</option>
              {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select></div>
          <div className="form-group"><label>Date</label><input type="date" value={form.date} onChange={e => set('date', e.target.value)} /></div>
          <div className="form-group"><label>Expected Date</label><input type="date" value={form.expected_date} onChange={e => set('expected_date', e.target.value)} /></div>
        </div>

        <h4 style={{margin:'1rem 0 .5rem'}}>Line Items</h4>
        <table className="line-items-table">
          <thead><tr><th style={{width:'30%'}}>Product</th><th>Description</th><th style={{width:'8%'}}>Qty</th><th style={{width:'10%'}}>Price</th><th style={{width:'8%'}}>Disc %</th><th style={{width:'8%'}}>Tax %</th><th style={{width:'10%'}}>Total</th><th style={{width:'3%'}}></th></tr></thead>
          <tbody>
            {items.map(item => (
              <tr key={item.key}>
                <td><select value={item.product_id} onChange={e => updateItem(item.key, 'product_id', e.target.value)}>
                  <option value="">Select product</option>{products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select></td>
                <td><input value={item.description} onChange={e => updateItem(item.key, 'description', e.target.value)} /></td>
                <td><input type="number" min="1" value={item.quantity} onChange={e => updateItem(item.key, 'quantity', e.target.value)} /></td>
                <td><input type="number" step="0.01" value={item.unit_price} onChange={e => updateItem(item.key, 'unit_price', e.target.value)} /></td>
                <td><input type="number" step="0.01" value={item.discount_pct} onChange={e => updateItem(item.key, 'discount_pct', e.target.value)} /></td>
                <td><input type="number" step="0.01" value={item.tax_rate} onChange={e => updateItem(item.key, 'tax_rate', e.target.value)} /></td>
                <td style={{textAlign:'right',fontWeight:500}}>${calcLineTotal(item).toFixed(2)}</td>
                <td><button className="remove-row" onClick={() => removeItem(item.key)}><X size={14} /></button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <button className="btn btn-secondary" style={{marginTop:'.5rem'}} onClick={addItem}><Plus size={14} /> Add Line</button>

        <div className="document-totals">
          <table className="totals-table"><tbody>
            <tr><td className="total-label">Discount:</td><td className="total-value">
              <input type="number" step="0.01" style={{width:100,textAlign:'right'}} value={form.discount_amount} onChange={e => set('discount_amount', e.target.value)} />
            </td></tr>
            <tr className="grand-total"><td className="total-label">Total:</td><td className="total-value">${grandTotal.toFixed(2)}</td></tr>
          </tbody></table>
        </div>

        <div className="form-grid" style={{marginTop:'.75rem'}}>
          <div className="form-group full"><label>Notes</label><textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} /></div>
        </div>
      </div>
      <div className="card-footer">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave({
          ...form, items: items.map(i => ({
            product_id: i.product_id, description: i.description, quantity: i.quantity,
            unit_price: i.unit_price, discount_pct: i.discount_pct, tax_rate: i.tax_rate,
          }))
        })} disabled={!form.supplier_id || !form.warehouse_id}>Save</button>
      </div>
    </div>
  );
}

/* ─── Supplier Form ─── */
function SupplierForm({ supplier, onSave, onCancel }) {
  const [form, setForm] = useState({
    name: supplier?.name || '', email: supplier?.email || '',
    phone: supplier?.phone || '', company: supplier?.company || '',
    address: supplier?.address || '', tax_id: supplier?.tax_id || '',
    payment_terms: supplier?.payment_terms || '',
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  return (
    <div className="erp-form card">
      <div className="card-header"><h3>{supplier ? 'Edit' : 'New'} Supplier</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button></div>
      <div className="card-body form-grid">
        <div className="form-group"><label>Name *</label><input value={form.name} onChange={e => set('name', e.target.value)} /></div>
        <div className="form-group"><label>Email</label><input type="email" value={form.email} onChange={e => set('email', e.target.value)} /></div>
        <div className="form-group"><label>Phone</label><input value={form.phone} onChange={e => set('phone', e.target.value)} /></div>
        <div className="form-group"><label>Company</label><input value={form.company} onChange={e => set('company', e.target.value)} /></div>
        <div className="form-group"><label>Tax ID</label><input value={form.tax_id} onChange={e => set('tax_id', e.target.value)} /></div>
        <div className="form-group"><label>Payment Terms</label><input value={form.payment_terms} onChange={e => set('payment_terms', e.target.value)} /></div>
        <div className="form-group full"><label>Address</label><textarea value={form.address} onChange={e => set('address', e.target.value)} rows={2} /></div>
      </div>
      <div className="card-footer">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)}>Save</button>
      </div>
    </div>
  );
}

/* ─── Receive Goods Modal ─── */
function ReceiveModal({ po, onReceive, onClose }) {
  const receivable = (po.items || []).filter(i => parseFloat(i.received_qty || 0) < parseFloat(i.quantity));
  const [quantities, setQuantities] = useState(
    Object.fromEntries(receivable.map(i => [i.id, 0]))
  );
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{maxWidth:600}} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Receive Goods — {po.number}</h3>
          <button className="btn-icon" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          {receivable.length === 0 ? <p>All items fully received.</p> : (
            <table className="data-table">
              <thead><tr><th>Product</th><th>Ordered</th><th>Already Received</th><th>Receive Now</th></tr></thead>
              <tbody>
                {receivable.map(item => {
                  const remaining = parseFloat(item.quantity) - parseFloat(item.received_qty || 0);
                  return (
                    <tr key={item.id}>
                      <td>{item.product_name || item.description}</td>
                      <td>{item.quantity}</td>
                      <td>{item.received_qty || 0}</td>
                      <td><input type="number" min={0} max={remaining} style={{width:80}}
                        value={quantities[item.id] || 0}
                        onChange={e => setQuantities(q => ({...q, [item.id]: Math.min(parseFloat(e.target.value)||0, remaining)}))} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-success"
            onClick={() => onReceive(Object.entries(quantities).filter(([,q]) => q > 0).map(([id, quantity]) => ({ item_id: id, quantity })))}
            disabled={!Object.values(quantities).some(q => q > 0)}>
            <CheckCircle size={16} /> Confirm Receipt
          </button>
        </div>
      </div>
    </div>
  );
}

export default PurchasingPage;
