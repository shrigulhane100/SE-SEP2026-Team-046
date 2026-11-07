import { api, setToken } from '../api/client';
export const authService = {
  async login(email, password) { const r = await api.post('/auth/login', { email, password }); setToken(r.access_token); return r.user; },
  async register(data) { const r = await api.post('/auth/register', data); setToken(r.access_token); return r.user; },
  me: () => api.get('/auth/me'),
  logout: () => setToken(null),
  updateMe: (data) => api.patch('/auth/me', data),
  changePassword: (current_password, new_password) => api.post('/auth/change-password', { current_password, new_password }),
  resetDemo: () => api.post('/dev/reset'),
};
