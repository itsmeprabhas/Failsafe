import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors SMOOTHLY (No more hard page reloads!)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  // OAuth2PasswordRequestForm requires application/x-www-form-urlencoded
  login: (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me'),
};

// Upload APIs
export const uploadAPI = {
  uploadCSV: (file, metadata) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/upload/csv?batch_name=${metadata.batch_name}&semester=${metadata.semester}&academic_year=${metadata.academic_year}&subject=${metadata.subject}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadManual: (data) => api.post('/upload/manual', data),
  getBatches: () => api.get('/upload/batches'),
};

// Prediction APIs
export const predictionAPI = {
  runPredictions: (batchId) => api.post(`/predictions/run/${batchId}`),
  getStudentPrediction: (studentRecordId) => api.get(`/predictions/student/${studentRecordId}`),
  getAutoInterventions: (batchId) => api.get(`/predictions/interventions/${batchId}`),
};

// Intervention APIs
export const interventionAPI = {
  create: (data) => api.post('/interventions/', data),
  getByStudent: (studentRecordId) => api.get(`/interventions/student/${studentRecordId}`),
  update: (id, data) => api.put(`/interventions/${id}`, data),
  getAll: (status) => api.get(`/interventions/${status ? `?status=${status}` : ''}`),
  getStats: () => api.get('/interventions/stats'),
};

// Dashboard APIs
export const dashboardAPI = {
  getOverview: () => api.get('/dashboard/overview'),
  getRiskTrends: (days = 30) => api.get(`/dashboard/risk-trends?days=${days}`),
  getDepartmentAnalysis: () => api.get('/dashboard/department-analysis'),
  getTopRiskStudents: (limit = 10) => api.get(`/dashboard/top-risk-students?limit=${limit}`),
};

// Admin / Reset APIs
export const adminAPI = {
  resetPredictions:  () => api.delete('/admin/reset/predictions'),
  resetInterventions:() => api.delete('/admin/reset/interventions'),
  resetStudentData:  () => api.delete('/admin/reset/student-data'),
  resetAll:          () => api.delete('/admin/reset/all'),
};

export default api;

