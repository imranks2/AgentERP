import React, { useState, useEffect, useCallback } from 'react';
import { inventoryAPI } from '../services/api';
import analytics from '../services/analytics';
import {
  Box, Plus, Search, Edit3, Trash2, Warehouse, Tag,
  ArrowUpDown, AlertCircle, Check, RefreshCw, X,
} from 'lucide-react';
import '../styles/erp.css';

function InventoryPage() {
  const [tab, setTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [stockModal, setStockModal] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [prodRes, catRes, whRes, statRes] = await Promise.all([
        inventoryAPI.listProducts({ search }).catch(() => ({ data: { products: [] } })),
        inventoryAPI.listCategories().catch(() => ({ data: { categories: [] } })),
        inventoryAPI.listWarehouses().catch(() => ({ data: { warehouses: [] } })),
        inventoryAPI.stats().catch(() => ({ data: { stats: {} } })),
      ]);
      setProducts(prodRes.data.products || []);
      setCategories(catRes.data.categories || []);
      setWarehouses(whRes.data.warehouses || []);
      setStats(statRes.data.stats || {});
    } catch (err) {
      setError('Failed to load inventory data');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { analytics.pageView('inventory'); loadData(); }, [loadData]);

  const clearMessages = () => { setError(null); setSuccess(null); };

  // ── Product CRUD ──
  const handleSaveProduct = async (data) => {
    clearMessages();
    try {
      if (editItem) {
        await inventoryAPI.updateProduct(editItem.id, data);
        setSuccess('Product updated');
      } else {
        await inventoryAPI.createProduct(data);
        setSuccess('Product created');
      }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  const handleDeleteProduct = async (id) => {
    if (!window.confirm('Delete this product?')) return;
    try {
      await inventoryAPI.deleteProduct(id);
      setSuccess('Product deleted'); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Delete failed'); }
  };

  // ── Category CRUD ──
  const handleSaveCategory = async (data) => {
    clearMessages();
    try {
      if (editItem) {
        await inventoryAPI.updateCategory(editItem.id, data);
        setSuccess('Category updated');
      } else {
        await inventoryAPI.createCategory(data);
        setSuccess('Category created');
      }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  // ── Warehouse CRUD ──
  const handleSaveWarehouse = async (data) => {
    clearMessages();
    try {
      if (editItem) {
        await inventoryAPI.updateWarehouse(editItem.id, data);
        setSuccess('Warehouse updated');
      } else {
        await inventoryAPI.createWarehouse(data);
        setSuccess('Warehouse created');
      }
      setShowForm(false); setEditItem(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  // ── Stock Adjust ──
  const handleAdjustStock = async (data) => {
    clearMessages();
    try {
      await inventoryAPI.adjustStock(data);
      setSuccess('Stock adjusted'); setStockModal(null); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Adjust failed'); }
  };

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading inventory...</p></div>;

  return (
    <div className="erp-page">
      <header className="page-header">
        <div>
          <h1><Box size={24} /> Inventory</h1>
          <p className="header-subtitle">Products, categories, warehouses & stock</p>
        </div>
      </header>

      {error && <div className="alert alert-danger"><AlertCircle size={16} /> {error} <button className="alert-close" onClick={() => setError(null)}>&times;</button></div>}
      {success && <div className="alert alert-success"><Check size={16} /> {success} <button className="alert-close" onClick={() => setSuccess(null)}>&times;</button></div>}

      {/* Stats */}
      {stats && (
        <div className="stat-grid sm">
          <div className="stat-card stat-blue"><div className="stat-card-header"><span className="stat-card-label">Products</span></div><div className="stat-card-value">{stats.total_products}</div></div>
          <div className="stat-card stat-green"><div className="stat-card-header"><span className="stat-card-label">Categories</span></div><div className="stat-card-value">{stats.total_categories}</div></div>
          <div className="stat-card stat-purple"><div className="stat-card-header"><span className="stat-card-label">Warehouses</span></div><div className="stat-card-value">{stats.total_warehouses}</div></div>
          <div className="stat-card stat-orange"><div className="stat-card-header"><span className="stat-card-label">Total Stock</span></div><div className="stat-card-value">{stats.total_stock_qty}</div></div>
        </div>
      )}

      {/* Tabs */}
      <div className="erp-tabs">
        {[
          { key: 'products', label: 'Products', icon: Box },
          { key: 'categories', label: 'Categories', icon: Tag },
          { key: 'warehouses', label: 'Warehouses', icon: Warehouse },
          { key: 'movements', label: 'Stock Movements', icon: ArrowUpDown },
        ].map(t => (
          <button key={t.key} className={`erp-tab ${tab === t.key ? 'active' : ''}`}
            onClick={() => { setTab(t.key); setShowForm(false); setEditItem(null); }}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* ── Products Tab ── */}
      {tab === 'products' && (
        <div className="erp-section">
          <div className="section-toolbar">
            <div className="search-bar compact">
              <Search size={16} />
              <input placeholder="Search products..." value={search}
                onChange={e => setSearch(e.target.value)} />
            </div>
            <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditItem(null); }}>
              <Plus size={16} /> Add Product
            </button>
          </div>
          {showForm && (
            <ProductForm product={editItem} categories={categories}
              onSave={handleSaveProduct} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr>
                <th>Name</th><th>SKU</th><th>Type</th><th>Sale Price</th><th>Cost Price</th><th>Category</th><th>Actions</th>
              </tr></thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id}>
                    <td className="fw-medium">{p.name}</td>
                    <td>{p.sku || '-'}</td>
                    <td><span className="badge badge-info">{p.product_type}</span></td>
                    <td>${parseFloat(p.sale_price).toFixed(2)}</td>
                    <td>${parseFloat(p.cost_price).toFixed(2)}</td>
                    <td>{p.category_name || '-'}</td>
                    <td className="actions-cell">
                      <button className="btn-icon" title="Edit" onClick={() => { setEditItem(p); setShowForm(true); }}><Edit3 size={15} /></button>
                      <button className="btn-icon" title="Adjust Stock" onClick={() => setStockModal(p)}><ArrowUpDown size={15} /></button>
                      <button className="btn-icon danger" title="Delete" onClick={() => handleDeleteProduct(p.id)}><Trash2 size={15} /></button>
                    </td>
                  </tr>
                ))}
                {products.length === 0 && <tr><td colSpan={7} className="empty-row">No products found</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Categories Tab ── */}
      {tab === 'categories' && (
        <div className="erp-section">
          <div className="section-toolbar">
            <span />
            <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditItem(null); }}>
              <Plus size={16} /> Add Category
            </button>
          </div>
          {showForm && (
            <CategoryForm category={editItem} categories={categories}
              onSave={handleSaveCategory} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Name</th><th>Slug</th><th>Parent</th><th>Actions</th></tr></thead>
              <tbody>
                {categories.map(c => (
                  <tr key={c.id}>
                    <td className="fw-medium">{c.name}</td>
                    <td>{c.slug}</td>
                    <td>{c.parent_name || '-'}</td>
                    <td className="actions-cell">
                      <button className="btn-icon" onClick={() => { setEditItem(c); setShowForm(true); }}><Edit3 size={15} /></button>
                    </td>
                  </tr>
                ))}
                {categories.length === 0 && <tr><td colSpan={4} className="empty-row">No categories</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Warehouses Tab ── */}
      {tab === 'warehouses' && (
        <div className="erp-section">
          <div className="section-toolbar">
            <span />
            <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditItem(null); }}>
              <Plus size={16} /> Add Warehouse
            </button>
          </div>
          {showForm && (
            <WarehouseForm warehouse={editItem}
              onSave={handleSaveWarehouse} onCancel={() => { setShowForm(false); setEditItem(null); }} />
          )}
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Name</th><th>Code</th><th>Address</th><th>Actions</th></tr></thead>
              <tbody>
                {warehouses.map(w => (
                  <tr key={w.id}>
                    <td className="fw-medium">{w.name}</td>
                    <td>{w.code || '-'}</td>
                    <td>{w.address || '-'}</td>
                    <td className="actions-cell">
                      <button className="btn-icon" onClick={() => { setEditItem(w); setShowForm(true); }}><Edit3 size={15} /></button>
                    </td>
                  </tr>
                ))}
                {warehouses.length === 0 && <tr><td colSpan={4} className="empty-row">No warehouses</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Movements Tab ── */}
      {tab === 'movements' && <StockMovements />}

      {/* ── Stock Adjust Modal ── */}
      {stockModal && (
        <StockAdjustModal product={stockModal} warehouses={warehouses}
          onSave={handleAdjustStock} onClose={() => setStockModal(null)} />
      )}
    </div>
  );
}

/* ─── Sub-components (forms) ─── */

function ProductForm({ product, categories, onSave, onCancel }) {
  const [form, setForm] = useState({
    name: product?.name || '', sku: product?.sku || '',
    product_type: product?.product_type || 'goods',
    sale_price: product?.sale_price || '', cost_price: product?.cost_price || '',
    tax_rate: product?.tax_rate ?? '0', category_id: product?.category_id || '',
    description: product?.description || '', uom: product?.uom || 'unit',
    reorder_point: product?.reorder_point || 0,
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  return (
    <div className="erp-form card">
      <div className="card-header"><h3>{product ? 'Edit' : 'New'} Product</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button></div>
      <div className="card-body form-grid">
        <div className="form-group"><label>Name *</label><input value={form.name} onChange={e => set('name', e.target.value)} /></div>
        <div className="form-group"><label>SKU</label><input value={form.sku} onChange={e => set('sku', e.target.value)} /></div>
        <div className="form-group"><label>Type</label>
          <select value={form.product_type} onChange={e => set('product_type', e.target.value)}>
            <option value="goods">Goods</option><option value="service">Service</option><option value="consumable">Consumable</option>
          </select></div>
        <div className="form-group"><label>Category</label>
          <select value={form.category_id} onChange={e => set('category_id', e.target.value)}>
            <option value="">None</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select></div>
        <div className="form-group"><label>Sale Price</label><input type="number" step="0.01" value={form.sale_price} onChange={e => set('sale_price', e.target.value)} /></div>
        <div className="form-group"><label>Cost Price</label><input type="number" step="0.01" value={form.cost_price} onChange={e => set('cost_price', e.target.value)} /></div>
        <div className="form-group"><label>Tax Rate %</label><input type="number" step="0.01" value={form.tax_rate} onChange={e => set('tax_rate', e.target.value)} /></div>
        <div className="form-group"><label>UoM</label><input value={form.uom} onChange={e => set('uom', e.target.value)} /></div>
        <div className="form-group"><label>Reorder Point</label><input type="number" value={form.reorder_point} onChange={e => set('reorder_point', e.target.value)} /></div>
        <div className="form-group full"><label>Description</label><textarea value={form.description} onChange={e => set('description', e.target.value)} rows={2} /></div>
      </div>
      <div className="card-footer">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)}>Save</button>
      </div>
    </div>
  );
}

function CategoryForm({ category, categories, onSave, onCancel }) {
  const [form, setForm] = useState({ name: category?.name || '', parent_id: category?.parent_id || '', description: category?.description || '' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  return (
    <div className="erp-form card">
      <div className="card-header"><h3>{category ? 'Edit' : 'New'} Category</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button></div>
      <div className="card-body form-grid">
        <div className="form-group"><label>Name *</label><input value={form.name} onChange={e => set('name', e.target.value)} /></div>
        <div className="form-group"><label>Parent</label>
          <select value={form.parent_id} onChange={e => set('parent_id', e.target.value)}>
            <option value="">None (root)</option>
            {categories.filter(c => c.id !== category?.id).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select></div>
        <div className="form-group full"><label>Description</label><textarea value={form.description} onChange={e => set('description', e.target.value)} rows={2} /></div>
      </div>
      <div className="card-footer">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)}>Save</button>
      </div>
    </div>
  );
}

function WarehouseForm({ warehouse, onSave, onCancel }) {
  const [form, setForm] = useState({ name: warehouse?.name || '', code: warehouse?.code || '', address: warehouse?.address || '' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  return (
    <div className="erp-form card">
      <div className="card-header"><h3>{warehouse ? 'Edit' : 'New'} Warehouse</h3>
        <button className="btn-icon" onClick={onCancel}><X size={18} /></button></div>
      <div className="card-body form-grid">
        <div className="form-group"><label>Name *</label><input value={form.name} onChange={e => set('name', e.target.value)} /></div>
        <div className="form-group"><label>Code</label><input value={form.code} onChange={e => set('code', e.target.value)} /></div>
        <div className="form-group full"><label>Address</label><textarea value={form.address} onChange={e => set('address', e.target.value)} rows={2} /></div>
      </div>
      <div className="card-footer">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)}>Save</button>
      </div>
    </div>
  );
}

function StockAdjustModal({ product, warehouses, onSave, onClose }) {
  const [form, setForm] = useState({ warehouse_id: '', quantity: 0, movement_type: 'adjustment', notes: '' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Adjust Stock: {product.name}</h3>
          <button className="btn-icon" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body form-grid">
          <div className="form-group"><label>Warehouse *</label>
            <select value={form.warehouse_id} onChange={e => set('warehouse_id', e.target.value)}>
              <option value="">Select warehouse</option>
              {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select></div>
          <div className="form-group"><label>Quantity (+/-)</label>
            <input type="number" value={form.quantity} onChange={e => set('quantity', parseInt(e.target.value) || 0)} /></div>
          <div className="form-group"><label>Type</label>
            <select value={form.movement_type} onChange={e => set('movement_type', e.target.value)}>
              <option value="adjustment">Adjustment</option><option value="purchase">Purchase</option><option value="sale">Sale</option><option value="return">Return</option><option value="transfer">Transfer</option>
            </select></div>
          <div className="form-group full"><label>Notes</label><textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} /></div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={() => onSave({ ...form, product_id: product.id })} disabled={!form.warehouse_id}>Adjust</button>
        </div>
      </div>
    </div>
  );
}

function StockMovements() {
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    inventoryAPI.getMovements({}).then(r => setMovements(r.data.movements || [])).catch(() => {}).finally(() => setLoading(false));
  }, []);
  if (loading) return <p>Loading movements...</p>;
  return (
    <div className="erp-section">
      <div className="data-table-wrap">
        <table className="data-table">
          <thead><tr><th>Date</th><th>Product</th><th>Warehouse</th><th>Type</th><th>Qty</th><th>Reference</th></tr></thead>
          <tbody>
            {movements.map(m => (
              <tr key={m.id}>
                <td>{new Date(m.created_at).toLocaleDateString()}</td>
                <td>{m.product_name || m.product_id}</td>
                <td>{m.warehouse_name || m.warehouse_id}</td>
                <td><span className="badge badge-info">{m.movement_type}</span></td>
                <td className={m.quantity > 0 ? 'text-success' : 'text-danger'}>{m.quantity > 0 ? '+' : ''}{m.quantity}</td>
                <td>{m.reference_type ? `${m.reference_type}` : '-'}</td>
              </tr>
            ))}
            {movements.length === 0 && <tr><td colSpan={6} className="empty-row">No stock movements</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default InventoryPage;
