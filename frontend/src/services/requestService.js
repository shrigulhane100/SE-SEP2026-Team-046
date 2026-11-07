import { api } from '../api/client';
export const requestService = {
  create: (data) => api.post('/requests', data),
  list: (status) => api.get('/requests', { status }),
  accept: (id) => api.post(`/requests/${id}/accept`),
  reject: (id, reason) => api.post(`/requests/${id}/reject`, { reason }),
  cancel: (id) => api.post(`/requests/${id}/cancel`),
};
