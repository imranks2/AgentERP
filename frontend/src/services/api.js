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

// Users & RBAC API
export const usersAPI = {
  list: (params) => api.get('/users/', { params }),
  get: (id) => api.get(`/users/${id}`),
  invite: (data) => api.post('/users/invite', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  activate: (id, isActive) => api.put(`/users/${id}/activate`, { is_active: isActive }),
  delete: (id) => api.delete(`/users/${id}`),
  updateProfile: (data) => api.put('/users/profile', data),
  listRoles: () => api.get('/users/roles'),
  listPermissions: () => api.get('/users/permissions'),
  seedRoles: () => api.post('/users/seed-roles'),
  auditLogs: (params) => api.get('/users/audit-logs', { params }),
};

// Events & Notifications API
export const eventsAPI = {
  history: (params) => api.get('/events/history', { params }),
  replay: (data) => api.post('/events/replay', data),
  notifications: (params) => api.get('/events/notifications', { params }),
  unreadCount: () => api.get('/events/notifications/unread-count'),
  markRead: (id) => api.put(`/events/notifications/${id}/read`),
  markAllRead: () => api.put('/events/notifications/read-all'),
};

// Schema API
export const schemaAPI = {
  listSchemas: () => api.get('/schemas/'),
  getFormSchema: (entity) => api.get(`/schemas/forms/${entity}`),
  getTableSchema: (entity) => api.get(`/schemas/tables/${entity}`),
};

// AI API
export const aiAPI = {
  createConversation: (title) => api.post('/ai/conversations', { title }),
  listConversations: (params) => api.get('/ai/conversations', { params }),
  getConversation: (id) => api.get(`/ai/conversations/${id}`),
  sendMessage: (conversationId, content) =>
    api.post(`/ai/conversations/${conversationId}/messages`, { content }),
  deleteConversation: (id) => api.delete(`/ai/conversations/${id}`),
  query: (q) => api.post('/ai/query', { query: q }),
  submitFeedback: (interactionId, feedback) =>
    api.post(`/ai/interactions/${interactionId}/feedback`, { feedback }),
  listTools: () => api.get('/ai/tools'),
};

// Accounting API
export const accountingAPI = {
  listAccounts: (params) => api.get('/accounting/accounts', { params }),
  getAccount: (id) => api.get(`/accounting/accounts/${id}`),
  createAccount: (data) => api.post('/accounting/accounts', data),
  updateAccount: (id, data) => api.put(`/accounting/accounts/${id}`, data),
  deleteAccount: (id) => api.delete(`/accounting/accounts/${id}`),
  listFiscalYears: () => api.get('/accounting/fiscal-years'),
  createFiscalYear: (data) => api.post('/accounting/fiscal-years', data),
  getFiscalYear: (id) => api.get(`/accounting/fiscal-years/${id}`),
  closeFiscalYear: (id) => api.post(`/accounting/fiscal-years/${id}/close`),
  listJournalEntries: (params) => api.get('/accounting/journal-entries', { params }),
  getJournalEntry: (id) => api.get(`/accounting/journal-entries/${id}`),
  createJournalEntry: (data) => api.post('/accounting/journal-entries', data),
  postJournalEntry: (id) => api.post(`/accounting/journal-entries/${id}/post`),
  reverseJournalEntry: (id) => api.post(`/accounting/journal-entries/${id}/reverse`),
  listTaxRates: () => api.get('/accounting/tax-rates'),
  createTaxRate: (data) => api.post('/accounting/tax-rates', data),
  updateTaxRate: (id, data) => api.put(`/accounting/tax-rates/${id}`, data),
  listCurrencies: () => api.get('/accounting/currencies'),
  createCurrency: (data) => api.post('/accounting/currencies', data),
  updateCurrency: (id, data) => api.put(`/accounting/currencies/${id}`, data),
  trialBalance: (params) => api.get('/accounting/reports/trial-balance', { params }),
  profitAndLoss: (params) => api.get('/accounting/reports/profit-loss', { params }),
  balanceSheet: (params) => api.get('/accounting/reports/balance-sheet', { params }),
  stats: () => api.get('/accounting/stats'),
};

// CRM API
export const crmAPI = {
  listLeads: (params) => api.get('/crm/leads', { params }),
  getLead: (id) => api.get(`/crm/leads/${id}`),
  createLead: (data) => api.post('/crm/leads', data),
  updateLead: (id, data) => api.put(`/crm/leads/${id}`, data),
  deleteLead: (id) => api.delete(`/crm/leads/${id}`),
  convertLead: (id, customerId) => api.post(`/crm/leads/${id}/convert`, { customer_id: customerId }),
  listOpportunities: (params) => api.get('/crm/opportunities', { params }),
  getOpportunity: (id) => api.get(`/crm/opportunities/${id}`),
  createOpportunity: (data) => api.post('/crm/opportunities', data),
  updateOpportunity: (id, data) => api.put(`/crm/opportunities/${id}`, data),
  deleteOpportunity: (id) => api.delete(`/crm/opportunities/${id}`),
  listActivities: (params) => api.get('/crm/activities', { params }),
  createActivity: (data) => api.post('/crm/activities', data),
  pipelineStats: () => api.get('/crm/pipeline'),
  stats: () => api.get('/crm/stats'),
};

// HR API
export const hrAPI = {
  listEmployees: (params) => api.get('/hr/employees', { params }),
  getEmployee: (id) => api.get(`/hr/employees/${id}`),
  createEmployee: (data) => api.post('/hr/employees', data),
  updateEmployee: (id, data) => api.put(`/hr/employees/${id}`, data),
  terminateEmployee: (id, data) => api.post(`/hr/employees/${id}/terminate`, data),
  listLeaveTypes: () => api.get('/hr/leave-types'),
  createLeaveType: (data) => api.post('/hr/leave-types', data),
  listLeaveRequests: (params) => api.get('/hr/leave-requests', { params }),
  createLeaveRequest: (data) => api.post('/hr/leave-requests', data),
  approveLeave: (id) => api.post(`/hr/leave-requests/${id}/approve`),
  rejectLeave: (id) => api.post(`/hr/leave-requests/${id}/reject`),
  listPayrollRuns: (params) => api.get('/hr/payroll-runs', { params }),
  getPayrollRun: (id) => api.get(`/hr/payroll-runs/${id}`),
  createPayrollRun: (data) => api.post('/hr/payroll-runs', data),
  processPayroll: (id) => api.post(`/hr/payroll-runs/${id}/process`),
  listAttendance: (params) => api.get('/hr/attendance', { params }),
  recordAttendance: (data) => api.post('/hr/attendance', data),
  updateAttendance: (id, data) => api.put(`/hr/attendance/${id}`, data),
  stats: () => api.get('/hr/stats'),
};

// ── Phase 9: Advanced AI APIs ────────────────────────────

export const aiAdvancedAPI = {
  // Suggestions
  listSuggestions: (params = {}) => api.get('/ai/suggestions', { params }),
  getSuggestion: (id) => api.get(`/ai/suggestions/${id}`),
  generateSuggestions: () => api.post('/ai/suggestions/generate'),
  acceptSuggestion: (id) => api.post(`/ai/suggestions/${id}/accept`),
  dismissSuggestion: (id) => api.post(`/ai/suggestions/${id}/dismiss`),
  suggestionStats: () => api.get('/ai/suggestions/stats'),

  // Agent Actions
  listActions: (params = {}) => api.get('/ai/actions', { params }),
  getAction: (id) => api.get(`/ai/actions/${id}`),
  proposeAction: (data) => api.post('/ai/actions', data),
  approveAction: (id) => api.post(`/ai/actions/${id}/approve`),
  rejectAction: (id) => api.post(`/ai/actions/${id}/reject`),
  executeAction: (id) => api.post(`/ai/actions/${id}/execute`),
  pendingActions: () => api.get('/ai/actions/pending'),
  actionStats: () => api.get('/ai/actions/stats'),

  // Patterns
  listPatterns: (params = {}) => api.get('/ai/patterns', { params }),
  detectPatterns: () => api.post('/ai/patterns/detect'),
  dismissPattern: (id) => api.post(`/ai/patterns/${id}/dismiss`),
  activatePattern: (id) => api.post(`/ai/patterns/${id}/activate`),

  // Workflows
  listWorkflows: (params = {}) => api.get('/ai/workflows', { params }),
  createWorkflow: (data) => api.post('/ai/workflows', data),
  toggleWorkflow: (id) => api.post(`/ai/workflows/${id}/toggle`),
  workflowStats: () => api.get('/ai/workflows/stats'),

  // Training Pipeline
  exportTrainingData: (data = {}) => api.post('/ai/training/export', data),
  listDatasets: (params = {}) => api.get('/ai/training/datasets', { params }),
  getDataset: (id) => api.get(`/ai/training/datasets/${id}`),
  trainModel: (data) => api.post('/ai/training/train', data),
  listModels: (params = {}) => api.get('/ai/training/models', { params }),
  activateModel: (id) => api.post(`/ai/training/models/${id}/activate`),
  trainingStats: () => api.get('/ai/training/stats'),
};

export default api;
