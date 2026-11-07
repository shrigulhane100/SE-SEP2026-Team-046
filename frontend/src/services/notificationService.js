import { api } from '../api/client';
export const notificationService = { list: () => api.get('/notifications'), read: (id) => api.post(`/notifications/${id}/read`), readAll: () => api.post('/notifications/read-all') };
