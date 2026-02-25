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

export default api;
