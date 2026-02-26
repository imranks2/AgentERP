import React, { useState, useEffect, useCallback } from 'react';
import { purchasingAPI, inventoryAPI } from '../services/api';
import analytics from '../services/analytics';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import TabBar from '../components/TabBar';
import StatCards from '../components/StatCards';
import Alert from '../components/Alert';
import PageHeader from '../components/PageHeader';
import LineItems from '../components/LineItems';
import { formatCurrency } from '../utils/formatters';
import { STATUS_CONFIG } from '../utils/constants';
import {
  Plus, Edit3, Eye, Package, Users,
  X, CheckCircle,
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

  const handleSaveSupplier = async (data) => {
    clearMsg();
    try {
      if (editItem) { await purchasingAPI.updateSupplier(editItem.id, data); setSuccess('Supplier updated'); }
      else { await purchasingAPI.createSupplier(data); setSuccess('Supplier created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  const handleSaveOrder = async (data) => {
    clearMsg();
    try {
      if (editItem) { await purchasingAPI.updateOrder(editItem.id, data); setSuccess('Order updated'); }
      else { await purchasingAPI.createOrder(data); setSuccess('Purchase order created'); }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  const handleReceiveGoods = async (poId, items) => {
    clearMsg();
    try {
      await purchasingAPI.receiveGoods(poId, { items });
      setSuccess('Goods received — stock updated');
      setReceiveModal(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Receive failed'); }
  };

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading purchasing...</p></div>;

  const statusBadge = (status) => {
    const cfg = STATUS_CONFIG[status] || {};
    return <span className="badge" style={{ background: cfg.bg, color: cfg.text }}>{cfg.label || status}</span>;
  };

  const orderCols = [
    { key: 'number', label: 'Number', sortable: true, render: (_, r) => <span className="fw-medium">{r.number}</span> },
    { key: 'supplier_name', label: 'Supplier', sortable: true },
    { key: 'total', label: 'Total', sortable: true, render: (v) => formatCurrency(v) },
    { key: 'status', label: 'Status', render: (v) => statusBadge(v) },
    { key: 'created_at', label: 'Date', sortable: true, render: (v) => v ? new Date(v).toLocaleDateString() : '' },
    { key: '_actions', label: 'Actions', render: (_, row) => (
      <div style={{ display: 'flex', gap: 4 }}>
        <button className="btn-icon" title="View" onClick={(e) => { e.stopPropagation(); setViewItem(row); }}><Eye size={15} /></button>
        {['draft', 'sent'].includes(row.status) && (
          <button className="btn-icon" title="Edit" onClick={(e) => { e.stopPropagation(); setEditItem(row); setShowForm(true); }}><Edit3 size={15} /></button>
        )}
        {['sent', 'partial'].includes(row.status) && (
          <button className="btn-icon" title="Receive" onClick={(e) => { e.stopPropagation(); setReceiveModal(row); }}><CheckCircle size={15} /></button>
        )}
      </div>
    )},
  ];
  const supplierCols = [
    { key: 'name', label: 'Name', sortable: true, render: (_, r) => <span className="fw-medium">{r.name}</span> },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'phone', label: 'Phone' },
    { key: 'company', label: 'Company', sortable: true },
    { key: '_actions', label: 'Actions', render: (_, row) => (
      <button className="btn-icon" onClick={(e) => { e.stopPropagation(); setEditItem(row); setShowForm(true); }}><Edit3 size={15} /></button>
    )},
  ];

  const tabs = [
    { key: 'orders', label: 'Purchase Orders', icon: <Package size={15} />, count: orders.length },
    { key: 'suppliers', label: 'Suppliers', icon: <Users size={15} />, count: suppliers.length },
  ];

  return (
    <div className="erp-page">
      <PageHeader title="Purchasing" subtitle="Suppliers, purchase orders & goods receipt"
        actions={
          <button className="btn btn-primary"
            onClick={() => { setShowForm(true); setEditItem(null); setViewItem(null); }}>
            <Plus size={16} /> {tab === 'suppliers' ? 'Add Supplier' : 'New Purchase Order'}
          </button>
        }
      />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {stats && (
        <StatCards stats={[
          { label: 'Suppliers', value: stats.total_suppliers, iconColor: 'blue' },
          { label: 'Orders', value: stats.total_orders, iconColor: 'purple' },
          { label: 'Total Value', value: formatCurrency(stats.total_value || 0), iconColor: 'green' },
          { label: 'Pending', value: stats.pending_orders, iconColor: 'orange' },
        ]} />
      )}

      <TabBar tabs={tabs} active={tab}
        onChange={(k) => { setTab(k); setShowForm(false); setEditItem(null); setViewItem(null); }} />

      {/* ── Purchase Orders ── */}
      {tab === 'orders' && !viewItem && (
        <div style={{ padding: '1rem 1.5rem' }}>
          {showForm && (
            <POForm po={editItem} suppliers={suppliers} products={products}
              warehouses={warehouses}
              onSave={handleSaveOrder} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <DataTable columns={orderCols} data={orders}
            emptyTitle="No purchase orders" emptyDesc="Create your first purchase order" />
        </div>
      )}

      {/* ── PO Detail ── */}
      {viewItem && (
        <div className="card" style={{ margin: '1rem 1.5rem' }}>
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
              <button className="btn btn-secondary" onClick={() => setViewItem(null)}>&larr; Back</button>
              <h3>{viewItem.number}</h3>
              {statusBadge(viewItem.status)}
            </div>
            {['sent', 'partial'].includes(viewItem.status) && (
              <button className="btn btn-success" onClick={() => setReceiveModal(viewItem)}>
                <CheckCircle size={16} /> Receive Goods
              </button>
            )}
          </div>
          <div className="card-body">
            <div className="df-grid cols-3" style={{ marginBottom: '1rem' }}>
              <div className="df-field"><label className="df-label">Supplier</label><div>{viewItem.supplier_name || '-'}</div></div>
              <div className="df-field"><label className="df-label">Date</label><div>{viewItem.date}</div></div>
              <div className="df-field"><label className="df-label">Warehouse</label><div>{viewItem.warehouse_name || '-'}</div></div>
            </div>
            {viewItem.items?.length > 0 && (
              <div className="li-table-wrap">
                <table className="li-table">
                  <thead><tr><th>#</th><th>Product</th><th>Ordered</th><th>Received</th><th>Price</th><th className="text-right">Total</th></tr></thead>
                  <tbody>
                    {viewItem.items.map((item, idx) => (
                      <tr key={item.id || idx}>
                        <td>{idx + 1}</td>
                        <td>{item.product_name || item.description}</td>
                        <td>{item.quantity}</td>
                        <td style={{ color: parseFloat(item.received_qty) >= parseFloat(item.quantity) ? 'var(--success)' : undefined }}>{item.received_qty || 0}</td>
                        <td>{formatCurrency(item.unit_price)}</td>
                        <td className="text-right">{formatCurrency(item.total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="li-totals">
              <table><tbody>
                <tr className="grand"><td className="label">Total:</td><td className="value">{formatCurrency(viewItem.total)}</td></tr>
              </tbody></table>
            </div>
          </div>
        </div>
      )}

      {/* ── Suppliers ── */}
      {tab === 'suppliers' && (
        <div style={{ padding: '1rem 1.5rem' }}>
          {showForm && (
            <SupplierForm supplier={editItem} onSave={handleSaveSupplier}
              onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <DataTable columns={supplierCols} data={suppliers}
            emptyTitle="No suppliers" emptyDesc="Add your first supplier" />
        </div>
      )}

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
    ? po.items.map(i => ({ ...i }))
    : [{ product_id: '', description: '', quantity: 1, unit_price: 0, discount_pct: 0, tax_rate: 0 }]
  );
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const updateItem = (idx, field, value) => {
    setItems(prev => prev.map((item, j) => {
      if (j !== idx) return item;
      const updated = { ...item, [field]: value };
      if (field === 'product_id' && value) {
        const prod = products.find(p => String(p.id) === String(value));
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
  const subtotal = items.reduce((sum, i) => sum + calcLineTotal(i), 0);
  const grandTotal = subtotal - (parseFloat(form.discount_amount) || 0);

  const liColumns = [
    { key: 'product_id', label: 'Product', type: 'select', width: '28%',
      options: products.map(p => ({ value: p.id, label: p.name })) },
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
        <h3>{po ? 'Edit' : 'New'} Purchase Order</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button>
      </div>
      <div className="card-body">
        <div className="df-grid cols-2" style={{ marginBottom: '1rem' }}>
          <div className="df-field"><label className="df-label">Supplier <span className="required">*</span></label>
            <select className="df-select" value={form.supplier_id} onChange={e => set('supplier_id', e.target.value)}>
              <option value="">Select supplier</option>
              {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}{s.company ? ` (${s.company})` : ''}</option>)}
            </select></div>
          <div className="df-field"><label className="df-label">Warehouse <span className="required">*</span></label>
            <select className="df-select" value={form.warehouse_id} onChange={e => set('warehouse_id', e.target.value)}>
              <option value="">Select warehouse</option>
              {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select></div>
          <div className="df-field"><label className="df-label">Date</label>
            <input className="df-input" type="date" value={form.date} onChange={e => set('date', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Expected Date</label>
            <input className="df-input" type="date" value={form.expected_date} onChange={e => set('expected_date', e.target.value)} /></div>
        </div>

        <LineItems
          columns={liColumns}
          rows={liRows}
          onChange={(idx, field, val) => updateItem(idx, field, val)}
          onAdd={() => setItems(i => [...i, { product_id: '', description: '', quantity: 1, unit_price: 0, discount_pct: 0, tax_rate: 0 }])}
          onRemove={(idx) => setItems(i => i.filter((_, j) => j !== idx))}
          totals={[
            { label: 'Subtotal', value: subtotal },
            { label: 'Discount', value: parseFloat(form.discount_amount) || 0 },
            { label: 'Total', value: grandTotal, grand: true },
          ]}
        />

        <div className="df-grid cols-1" style={{ marginTop: '1rem' }}>
          <div className="df-field"><label className="df-label">Notes</label><textarea className="df-textarea" value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} /></div>
        </div>
      </div>
      <div className="modal-dialog-footer">
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
    <div className="card" style={{ marginBottom: '1rem' }}>
      <div className="card-header"><h3>{supplier ? 'Edit' : 'New'} Supplier</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button></div>
      <div className="card-body">
        <div className="df-grid cols-2">
          <div className="df-field"><label className="df-label">Name <span className="required">*</span></label><input className="df-input" value={form.name} onChange={e => set('name', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Email</label><input className="df-input" type="email" value={form.email} onChange={e => set('email', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Phone</label><input className="df-input" value={form.phone} onChange={e => set('phone', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Company</label><input className="df-input" value={form.company} onChange={e => set('company', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Tax ID</label><input className="df-input" value={form.tax_id} onChange={e => set('tax_id', e.target.value)} /></div>
          <div className="df-field"><label className="df-label">Payment Terms</label><input className="df-input" value={form.payment_terms} onChange={e => set('payment_terms', e.target.value)} /></div>
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

/* ─── Receive Goods Modal ─── */
function ReceiveModal({ po, onReceive, onClose }) {
  const receivable = (po.items || []).filter(i => parseFloat(i.received_qty || 0) < parseFloat(i.quantity));
  const [quantities, setQuantities] = useState(
    Object.fromEntries(receivable.map(i => [i.id, 0]))
  );
  return (
    <Modal title={`Receive Goods — ${po.number}`} onClose={onClose} size="lg"
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-success"
            onClick={() => onReceive(Object.entries(quantities).filter(([, q]) => q > 0).map(([id, quantity]) => ({ item_id: id, quantity })))}
            disabled={!Object.values(quantities).some(q => q > 0)}>
            <CheckCircle size={16} /> Confirm Receipt
          </button>
        </>
      }
    >
      {receivable.length === 0 ? <p>All items fully received.</p> : (
        <div className="li-table-wrap">
          <table className="li-table">
            <thead><tr><th>Product</th><th>Ordered</th><th>Received</th><th>Receive Now</th></tr></thead>
            <tbody>
              {receivable.map(item => {
                const remaining = parseFloat(item.quantity) - parseFloat(item.received_qty || 0);
                return (
                  <tr key={item.id}>
                    <td>{item.product_name || item.description}</td>
                    <td>{item.quantity}</td>
                    <td>{item.received_qty || 0}</td>
                    <td><input type="number" min={0} max={remaining} style={{ width: 80 }}
                      value={quantities[item.id] || 0}
                      onChange={e => setQuantities(q => ({ ...q, [item.id]: Math.min(parseFloat(e.target.value) || 0, remaining) }))} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}

export default PurchasingPage;
