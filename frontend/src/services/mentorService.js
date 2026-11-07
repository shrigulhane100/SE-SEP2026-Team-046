import { api } from '../api/client';
export const mentorService = {
  list: (params) => api.get('/mentors', params),
  publicList: (params) => api.get('/public/mentors', params),
  get: (id) => api.get(`/mentors/${id}`),
  meta: () => api.get('/meta'),
  areas: () => api.get('/guidance-areas'),
};
