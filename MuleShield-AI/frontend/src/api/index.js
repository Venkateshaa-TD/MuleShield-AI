/**
 * MuleShield AI - API Service
 * Handles all communication with the backend API
 */

import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// ============================================
// DASHBOARD API
// ============================================

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
  getRiskDistribution: () => api.get('/dashboard/risk-distribution'),
  getRecentActivity: () => api.get('/dashboard/recent-activity'),
}

// ============================================
// ACCOUNTS API
// ============================================

export const accountsApi = {
  getAll: (params = {}) => api.get('/accounts', { params }),
  getById: (id) => api.get(`/accounts/${id}`),
  getRiskAnalysis: (id) => api.get(`/accounts/${id}/risk-analysis`),
  getNetwork: (id) => api.get(`/accounts/${id}/network`),
  getTransactions: (id, limit = 50) => api.get(`/accounts/${id}/transactions`, { params: { limit } }),
  getBehavioralProfile: (id) => api.get(`/accounts/${id}/behavioral-profile`),
}

// ============================================
// TRANSACTIONS API
// ============================================

export const transactionsApi = {
  getAll: (params = {}) => api.get('/transactions', { params }),
  getById: (id) => api.get(`/transactions/${id}`),
}

// ============================================
// ALERTS API
// ============================================

export const alertsApi = {
  getAll: (params = {}) => api.get('/alerts', { params }),
  getById: (id) => api.get(`/alerts/${id}`),
  update: (id, data) => api.put(`/alerts/${id}`, data),
}

// ============================================
// CASES API
// ============================================

export const casesApi = {
  getAll: (params = {}) => api.get('/cases', { params }),
  getById: (id) => api.get(`/cases/${id}`),
  create: (data) => api.post('/cases', data),
  update: (id, data) => api.put(`/cases/${id}`, data),
}

// ============================================
// NETWORK GRAPH API
// ============================================

export const graphApi = {
  getVisualization: (accountIds = null) => {
    const params = accountIds ? { account_ids: accountIds.join(',') } : {}
    return api.get('/graph/visualization', { params })
  },
  getPatterns: () => api.get('/graph/patterns'),
  getMuleNetwork: () => api.get('/graph/mule-network'),
}

// ============================================
// REPORTS API
// ============================================

export const reportsApi = {
  generateSAR: (accountId) => api.post(`/reports/sar/${accountId}`),
}

// ============================================
// ADAPTIVE LEARNING API
// ============================================

export const learningApi = {
  submitFeedback: (data) => api.post('/feedback', data),
  getWeights: () => api.get('/weights'),
}

// ============================================
// SYSTEM API
// ============================================

export const systemApi = {
  health: () => api.get('/health'),
  initialize: () => api.post('/initialize'),
}

export default api
