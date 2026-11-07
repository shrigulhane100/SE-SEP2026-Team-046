import { api } from '../api/client';
export const relationshipService = {
  list: () => api.get('/relationships'),
  get: (id) => api.get(`/relationships/${id}`),
  setStatus: (id, status) => api.patch(`/relationships/${id}/status`, { status }),
  addGoal: (id, title) => api.post(`/relationships/${id}/goals`, { title }),
  setGoalStatus: (goalId, status) => api.patch(`/goals/${goalId}`, { status }),
  addActivity: (id, data) => api.post(`/relationships/${id}/activities`, data),
  feedback: (id, data) => api.post(`/relationships/${id}/feedback`, data),
  report: (id, reason) => api.post(`/relationships/${id}/report`, { reason }),
  myFeedback: () => api.get('/feedback'),
};
