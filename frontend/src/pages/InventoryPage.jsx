import React, { useState, useEffect, useCallback } from 'react';
import { inventoryAPI } from '../services/api';
import analytics from '../services/analytics';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import TabBar from '../components/TabBar';
import StatCards from '../components/StatCards';
import Alert from '../components/Alert';
import PageHeader from '../components/PageHeader';
import {
  Box, Plus, Edit3, Trash2, Warehouse, Tag,
  ArrowUpDown, Package,
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
  const clearMsg = () => { setError(null); setSuccess(null); };
  const openForm = (item = null) => { setEditItem(item); setShowForm(true); };
  const closeForm = () => { setShowForm(false); setEditItem(null); };

  // ── Product CRUD ──
  const handleSaveProduct = async (data) => {
    clearMsg();
    try {
      if (editItem) { await inventoryAPI.updateProduct(editItem.id, data); setSuccess('Product updated'); }
      else { await inventoryAPI.createProduct(data); setSuccess('Product created'); }
      closeForm(); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  const handleDeleteProduct = async (id) => {
    if (!window.confirm('Delete this product?')) return;
    clearMsg();
    try { await inventoryAPI.deleteProduct(id); setSuccess('Product deleted'); loadData(); }
    catch (err) { setError(err.response?.data?.error || 'Delete failed'); }
  };

  // ── Category CRUD ──
  const handleSaveCategory = async (data) => {
    clearMsg();
    try {
      if (editItem) { await inventoryAPI.updateCategory(editItem.id, data); setSuccess('Category updated'); }
      else { await inventoryAPI.createCategory(data); setSuccess('Category created'); }
      closeForm(); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  // ── Warehouse CRUD ──
  const handleSaveWarehouse = async (data) => {
    clearMsg();
    try {
      if (editItem) { await inventoryAPI.updateWarehouse(editItem.id, data); setSuccess('Warehouse updated'); }
      else { await inventoryAPI.createWarehouse(data); setSuccess('Warehouse created'); }
      closeForm(); loadData();
    } catch (err) { setError(err.response?.data?.error || 'Save failed'); }
  };

  // ── Stock Adjust ──
  const handleAdjustStock = async (data) => {
    clearMsg();
    try { await inventoryAPI.adjustStock(data); setSuccess('Stock adjusted'); setStockModal(null); loadData(); }
    catch (err) { setError(err.response?.data?.error || 'Adjust failed'); }
  };

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading inventory...</p></div>;

  // ── Column definitions ──
  const productCols = [
    { key: 'name', label: 'Name', sortable: true, primary: true },
    { key: 'sku', label: 'SKU', sortable: true, render: (v) => v || '-' },
    { key: 'product_type', label: 'Type', sortable: true, render: (v) => <span className="badge badge-info">{v}</span> },
    { key: 'sale_price', label: 'Sale Price', sortable: true, align: 'right', render: (v) => `$${parseFloat(v).toFixed(2)}` },
    { key: 'cost_price', label: 'Cost Price', sortable: true, align: 'right', render: (v) => `$${parseFloat(v).toFixed(2)}` },
    { key: 'category_name', label: 'Category', render: (v) => v || '-' },
    { key: '_actions', label: 'Actions', render: (_, row) => (
      <div style={{ display: 'flex', gap: 4 }}>
        <button className="btn-icon" title="Edit" onClick={(e) => { e.stopPropagation(); openForm(row); }}><Edit3 size={15} /></button>
        <button className="btn-icon" title="Adjust Stock" onClick={(e) => { e.stopPropagation(); setStockModal(row); }}><ArrowUpDown size={15} /></button>
        <button className="btn-icon danger" title="Delete" onClick={(e) => { e.stopPropagation(); handleDeleteProduct(row.id); }}><Trash2 size={15} /></button>
      </div>
    )},
  ];

  const categoryCols = [
    { key: 'name', label: 'Name', sortable: true, primary: true },
    { key: 'slug', label: 'Slug', sortable: true },
    { key: 'parent_name', label: 'Parent', render: (v) => v || '-' },
    { key: '_actions', label: 'Actions', render: (_, row) => (
      <button className="btn-icon" onClick={() => openForm(row)}><Edit3 size={15} /></button>
    )},
  ];

  const warehouseCols = [
    { key: 'name', label: 'Name', sortable: true, primary: true },
    { key: 'code', label: 'Code', render: (v) => v || '-' },
    { key: 'address', label: 'Address', render: (v) => v || '-' },
    { key: '_actions', label: 'Actions', render: (_, row) => (
      <button className="btn-icon" onClick={() => openForm(row)}><Edit3 size={15} /></button>
    )},
  ];

  const tabs = [
    { key: 'products', label: 'Products', icon: Box, count: products.length },
    { key: 'categories', label: 'Categories', icon: Tag, count: categories.length },
    { key: 'warehouses', label: 'Warehouses', icon: Warehouse, count: warehouses.length },
    { key: 'movements', label: 'Stock Movements', icon: ArrowUpDown },
  ];

  const statItems = stats ? [
    { label: 'Products', value: stats.total_products, icon: Box, color: 'blue' },
    { label: 'Categories', value: stats.total_categories, icon: Tag, color: 'green' },
    { label: 'Warehouses', value: stats.total_warehouses, icon: Warehouse, color: 'purple' },
    { label: 'Total Stock', value: stats.total_stock_qty, icon: Package, color: 'orange' },
  ] : [];

  return (
    <div className="erp-page animate-fade-in">
      <PageHeader title="Inventory" subtitle="Products, categories, warehouses & stock" icon={Box}
        actions={
          <button className="btn btn-primary" onClick={() => openForm()}>
            <Plus size={16} /> {tab === 'products' ? 'Add Product' : tab === 'categories' ? 'Add Category' : tab === 'warehouses' ? 'Add Warehouse' : ''}
          </button>
        }
      />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      <StatCards stats={statItems} />

      <div style={{ padding: '0 1.5rem' }}>
        <TabBar tabs={tabs} active={tab} onChange={(k) => { setTab(k); closeForm(); }} />
      </div>

      <div style={{ padding: '1rem 1.5rem' }}>
        {tab === 'products' && (
          <DataTable
            columns={productCols} data={products} loading={loading}
            searchPlaceholder="Search products…"
            emptyTitle="No products" emptyDesc="Add your first product to get started"
            defaultSort={{ key: 'name', dir: 'asc' }}
          />
        )}

        {tab === 'categories' && (
          <DataTable
            columns={categoryCols} data={categories} loading={loading}
            searchPlaceholder="Search categories…"
            emptyTitle="No categories" emptyDesc="Create a category to organise products"
          />
        )}

        {tab === 'warehouses' && (
          <DataTable
            columns={warehouseCols} data={warehouses} loading={loading}
            searchPlaceholder="Search warehouses…"
            emptyTitle="No warehouses" emptyDesc="Add a warehouse to track stock"
          />
        )}

        {tab === 'movements' && <StockMovements />}
      </div>

      {/* ── Product / Category / Warehouse Form Modal ── */}
      {showForm && tab === 'products' && (
        <ProductFormModal product={editItem} categories={categories} onSave={handleSaveProduct} onClose={closeForm} />
      )}
      {showForm && tab === 'categories' && (
        <CategoryFormModal category={editItem} categories={categories} onSave={handleSaveCategory} onClose={closeForm} />
      )}
      {showForm && tab === 'warehouses' && (
        <WarehouseFormModal warehouse={editItem} onSave={handleSaveWarehouse} onClose={closeForm} />
      )}

      {/* Stock adjust modal */}
      {stockModal && (
        <StockAdjustModal product={stockModal} warehouses={warehouses} onSave={handleAdjustStock} onClose={() => setStockModal(null)} />
      )}
    </div>
  );
}

/* ─── Product Form Modal ─── */
function ProductFormModal({ product, categories, onSave, onClose }) {
  const [form, setForm] = useState({
    name: product?.name || '', sku: product?.sku || '',
    product_type: product?.product_type || 'goods',
    sale_price: product?.sale_price || '', cost_price: product?.cost_price || '',
    tax_rate: product?.tax_rate ?? '0', category_id: product?.category_id || '',
    description: product?.description || '', uom: product?.uom || 'unit',
    reorder_point: product?.reorder_point || 0,
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const schema = [
    { name: 'name', label: 'Name', required: true },
    { name: 'sku', label: 'SKU' },
    { name: 'product_type', label: 'Type', type: 'select', options: [
      { value: 'goods', label: 'Goods' }, { value: 'service', label: 'Service' }, { value: 'consumable', label: 'Consumable' },
    ]},
    { name: 'category_id', label: 'Category', type: 'select', placeholder: 'None', options: categories.map(c => ({ value: c.id, label: c.name })) },
    { name: 'sale_price', label: 'Sale Price', type: 'number', step: '0.01' },
    { name: 'cost_price', label: 'Cost Price', type: 'number', step: '0.01' },
    { name: 'tax_rate', label: 'Tax Rate %', type: 'number', step: '0.01' },
    { name: 'uom', label: 'UoM' },
    { name: 'reorder_point', label: 'Reorder Point', type: 'number' },
    { name: 'description', label: 'Description', type: 'textarea', full: true, rows: 2 },
  ];

  return (
    <Modal open={true} onClose={onClose} title={`${product ? 'Edit' : 'New'} Product`} size="lg"
      footer={<>
        <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)}>Save</button>
      </>}
    >
      <DynamicForm schema={schema} values={form} onChange={set} columns={2} />
    </Modal>
  );
}

/* ─── Category Form Modal ─── */
function CategoryFormModal({ category, categories, onSave, onClose }) {
  const [form, setForm] = useState({ name: category?.name || '', parent_id: category?.parent_id || '', description: category?.description || '' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const schema = [
    { name: 'name', label: 'Name', required: true },
    { name: 'parent_id', label: 'Parent', type: 'select', placeholder: 'None (root)',
      options: categories.filter(c => c.id !== category?.id).map(c => ({ value: c.id, label: c.name })) },
    { name: 'description', label: 'Description', type: 'textarea', full: true, rows: 2 },
  ];

  return (
    <Modal open={true} onClose={onClose} title={`${category ? 'Edit' : 'New'} Category`} size="md"
      footer={<>
        <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)}>Save</button>
      </>}
    >
      <DynamicForm schema={schema} values={form} onChange={set} columns={2} />
    </Modal>
  );
}

/* ─── Warehouse Form Modal ─── */
function WarehouseFormModal({ warehouse, onSave, onClose }) {
  const [form, setForm] = useState({ name: warehouse?.name || '', code: warehouse?.code || '', address: warehouse?.address || '' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const schema = [
    { name: 'name', label: 'Name', required: true },
    { name: 'code', label: 'Code' },
    { name: 'address', label: 'Address', type: 'textarea', full: true, rows: 2 },
  ];

  return (
    <Modal open={true} onClose={onClose} title={`${warehouse ? 'Edit' : 'New'} Warehouse`} size="md"
      footer={<>
        <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave(form)}>Save</button>
      </>}
    >
      <DynamicForm schema={schema} values={form} onChange={set} columns={2} />
    </Modal>
  );
}

/* ─── Stock Adjust Modal ─── */
function StockAdjustModal({ product, warehouses, onSave, onClose }) {
  const [form, setForm] = useState({ warehouse_id: '', quantity: 0, movement_type: 'adjustment', notes: '' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const schema = [
    { name: 'warehouse_id', label: 'Warehouse', type: 'select', required: true, placeholder: 'Select warehouse',
      options: warehouses.map(w => ({ value: w.id, label: w.name })) },
    { name: 'quantity', label: 'Quantity (+/-)', type: 'number' },
    { name: 'movement_type', label: 'Type', type: 'select', options: [
      { value: 'adjustment', label: 'Adjustment' }, { value: 'purchase', label: 'Purchase' },
      { value: 'sale', label: 'Sale' }, { value: 'return', label: 'Return' }, { value: 'transfer', label: 'Transfer' },
    ]},
    { name: 'notes', label: 'Notes', type: 'textarea', full: true, rows: 2 },
  ];

  return (
    <Modal open={true} onClose={onClose} title={`Adjust Stock: ${product.name}`} size="md"
      footer={<>
        <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSave({ ...form, product_id: product.id })} disabled={!form.warehouse_id}>Adjust</button>
      </>}
    >
      <DynamicForm schema={schema} values={form} onChange={set} columns={2} />
    </Modal>
  );
}

/* ─── Stock Movements ─── */
function StockMovements() {
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    inventoryAPI.getMovements({}).then(r => setMovements(r.data.movements || [])).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const cols = [
    { key: 'created_at', label: 'Date', sortable: true, render: (v) => new Date(v).toLocaleDateString() },
    { key: 'product_name', label: 'Product', primary: true, render: (v, row) => v || row.product_id },
    { key: 'warehouse_name', label: 'Warehouse', render: (v, row) => v || row.warehouse_id },
    { key: 'movement_type', label: 'Type', render: (v) => <span className="badge badge-info">{v}</span> },
    { key: 'quantity', label: 'Qty', render: (v) => <span className={v > 0 ? 'text-success' : 'text-danger'}>{v > 0 ? '+' : ''}{v}</span> },
    { key: 'reference_type', label: 'Reference', render: (v) => v || '-' },
  ];

  return (
    <DataTable
      columns={cols} data={movements} loading={loading}
      searchPlaceholder="Search movements…"
      emptyTitle="No stock movements" emptyDesc="Stock movements appear after inventory adjustments"
      defaultSort={{ key: 'created_at', dir: 'desc' }}
    />
  );
}

export default InventoryPage;
