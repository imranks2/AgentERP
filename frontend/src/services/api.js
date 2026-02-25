import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/refresh`, null, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          });
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  refresh: () => api.post('/auth/refresh'),
};

// Tenant API
export const tenantAPI = {
  list: (params) => api.get('/tenants/', { params }),
  get: (id) => api.get(`/tenants/${id}`),
  update: (id, data) => api.put(`/tenants/${id}`, data),
  changeStatus: (id, status) => api.put(`/tenants/${id}/status`, { status }),
  delete: (id) => api.delete(`/tenants/${id}`),
  stats: () => api.get('/tenants/stats'),
};

// Subscription API
export const subscriptionAPI = {
  listPlans: () => api.get('/subscriptions/plans'),
  subscribe: (planSlug, billingCycle) =>
    api.post('/subscriptions/subscribe', { plan_slug: planSlug, billing_cycle: billingCycle }),
  current: () => api.get('/subscriptions/current'),
  checkFeature: (featureKey) => api.get(`/subscriptions/check-feature/${featureKey}`),
  cancel: () => api.post('/subscriptions/cancel'),
};

// Admin API
export const adminAPI = {
  dashboard: () => api.get('/admin/dashboard'),
  listTenants: (params) => api.get('/admin/tenants', { params }),
  getTenant: (id) => api.get(`/admin/tenants/${id}`),
  updateTenantSubscription: (id, data) => api.put(`/admin/tenants/${id}/subscription`, data),
  platformConfig: () => api.get('/admin/platform-config'),
};

// Analytics API
export const analyticsAPI = {
  track: (data) => api.post('/analytics/track', data),
  events: (params) => api.get('/analytics/events', { params }),
  dashboard: (days) => api.get('/analytics/dashboard', { params: { days } }),
};

// Organisation API
export const organisationAPI = {
  tree: () => api.get('/organisation/tree'),
  list: (params) => api.get('/organisation/', { params }),
  stats: () => api.get('/organisation/stats'),
  get: (id) => api.get(`/organisation/${id}`),
  create: (data) => api.post('/organisation/', data),
  update: (id, data) => api.put(`/organisation/${id}`, data),
  delete: (id, reassignTo) =>
    api.delete(`/organisation/${id}`, { params: reassignTo ? { reassign_to: reassignTo } : {} }),
  move: (id, newParentId) =>
    api.put(`/organisation/${id}/move`, { new_parent_id: newParentId }),
  subtree: (id) => api.get(`/organisation/${id}/subtree`),
  ancestors: (id) => api.get(`/organisation/${id}/ancestors`),
};

// Modules API
export const modulesAPI = {
  available: () => api.get('/modules/available'),
  installed: () => api.get('/modules/installed'),
  install: (slug) => api.post(`/modules/${slug}/install`),
  uninstall: (slug) => api.post(`/modules/${slug}/uninstall`),
  seed: () => api.post('/modules/seed'),
};

// Inventory API
export const inventoryAPI = {
  // Categories
  listCategories: () => api.get('/inventory/categories'),
  createCategory: (data) => api.post('/inventory/categories', data),
  updateCategory: (id, data) => api.put(`/inventory/categories/${id}`, data),
  deleteCategory: (id) => api.delete(`/inventory/categories/${id}`),
  // Products
  listProducts: (params) => api.get('/inventory/products', { params }),
  getProduct: (id) => api.get(`/inventory/products/${id}`),
  createProduct: (data) => api.post('/inventory/products', data),
  updateProduct: (id, data) => api.put(`/inventory/products/${id}`, data),
  deleteProduct: (id) => api.delete(`/inventory/products/${id}`),
  // Warehouses
  listWarehouses: () => api.get('/inventory/warehouses'),
  createWarehouse: (data) => api.post('/inventory/warehouses', data),
  updateWarehouse: (id, data) => api.put(`/inventory/warehouses/${id}`, data),
  // Stock
  getStock: (params) => api.get('/inventory/stock', { params }),
  adjustStock: (data) => api.post('/inventory/stock/adjust', data),
  getMovements: (params) => api.get('/inventory/stock/movements', { params }),
  stats: () => api.get('/inventory/stats'),
};

// Sales API
export const salesAPI = {
  // Customers
  listCustomers: (params) => api.get('/sales/customers', { params }),
  getCustomer: (id) => api.get(`/sales/customers/${id}`),
  createCustomer: (data) => api.post('/sales/customers', data),
  updateCustomer: (id, data) => api.put(`/sales/customers/${id}`, data),
  // Quotations
  listQuotations: (params) => api.get('/sales/quotations', { params }),
  getQuotation: (id) => api.get(`/sales/quotations/${id}`),
  createQuotation: (data) => api.post('/sales/quotations', data),
  updateQuotation: (id, data) => api.put(`/sales/quotations/${id}`, data),
  convertQuotation: (id, data) => api.post(`/sales/quotations/${id}/convert`, data),
  // Invoices
  listInvoices: (params) => api.get('/sales/invoices', { params }),
  getInvoice: (id) => api.get(`/sales/invoices/${id}`),
  createInvoice: (data) => api.post('/sales/invoices', data),
  updateInvoiceStatus: (id, status) => api.put(`/sales/invoices/${id}/status`, { status }),
  // Payments
  listPayments: (invId) => api.get(`/sales/invoices/${invId}/payments`),
  recordPayment: (invId, data) => api.post(`/sales/invoices/${invId}/payments`, data),
  stats: () => api.get('/sales/stats'),
};

// Purchasing API
export const purchasingAPI = {
  // Suppliers
  listSuppliers: (params) => api.get('/purchasing/suppliers', { params }),
  getSupplier: (id) => api.get(`/purchasing/suppliers/${id}`),
  createSupplier: (data) => api.post('/purchasing/suppliers', data),
  updateSupplier: (id, data) => api.put(`/purchasing/suppliers/${id}`, data),
  // Purchase Orders
  listOrders: (params) => api.get('/purchasing/orders', { params }),
  getOrder: (id) => api.get(`/purchasing/orders/${id}`),
  createOrder: (data) => api.post('/purchasing/orders', data),
  updateOrder: (id, data) => api.put(`/purchasing/orders/${id}`, data),
  receiveGoods: (id, data) => api.post(`/purchasing/orders/${id}/receive`, data),
  stats: () => api.get('/purchasing/stats'),
};

export default api;
