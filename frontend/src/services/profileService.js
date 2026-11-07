import { api } from '../api/client';
export const profileService = { get: () => api.get('/profile/me'), save: (data) => api.put('/profile/me', data), dashboard: () => api.get('/dashboard') };
