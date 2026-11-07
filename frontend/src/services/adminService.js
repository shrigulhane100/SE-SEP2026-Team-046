import { api } from '../api/client';
export const adminService = {
  stats: (days) => api.get('/admin/stats', { days }),
  activity: () => api.get('/admin/activity'),
  users: (params) => api.get('/admin/users', params),
  setActive: (id, is_active) => api.patch(`/admin/users/${id}`, { is_active }),
  verifications: () => api.get('/admin/mentor-verifications'),
  verify: (id, approve) => api.post(`/admin/mentors/${id}/verify`, { approve }),
  requests: (params) => api.get('/admin/requests', params),
  relationships: (params) => api.get('/admin/relationships', params),
  reports: () => api.get('/admin/reports'),
  reviewReport: (id) => api.post(`/admin/reports/${id}/review`),
  areas: () => api.get('/admin/guidance-areas'),
  addArea: (name) => api.post('/admin/guidance-areas', { name }),
  setAreaActive: (id, is_active) => api.patch(`/admin/guidance-areas/${id}`, { is_active }),
};
