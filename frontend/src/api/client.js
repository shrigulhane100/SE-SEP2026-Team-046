import { handle } from './mockServer';
import { ApiError } from './errors';

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const TOKEN_KEY = 'rockstarz.token';
let token = null;
try { token = localStorage.getItem(TOKEN_KEY); } catch { /* ignore */ }
export const getToken = () => token;
export const setToken = (t) => { token = t; try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ } };
const clean = (o = {}) => Object.fromEntries(Object.entries(o).filter(([, v]) => v !== '' && v !== undefined && v !== null && v !== 'all'));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function request(method, path, { params, data } = {}) {
  let out;
  if (USE_MOCK) {
    await wait(120 + Math.random() * 180);
    try { out = structuredClone(handle({ method, path, params: clean(params), data: data || {}, token })); } catch (e) { out = e; }
    if (out instanceof Error) { if (out.status === 401) window.dispatchEvent(new Event('auth:expired')); throw out instanceof ApiError ? out : new ApiError(500, out.message); }
    return out;
  }
  const qs = new URLSearchParams(clean(params)).toString();
  let res;
  try {
    res = await fetch(`${BASE}${path}${qs ? '?' + qs : ''}`, { method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: data ? JSON.stringify(data) : undefined });
  } catch { throw new ApiError(0, 'Cannot reach the server. Check your connection.'); }
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    if (res.status === 401) window.dispatchEvent(new Event('auth:expired'));
    // FastAPI returns {detail: "..."} or {detail: [{msg}]} for validation errors
    throw new ApiError(res.status, typeof b.detail === 'string' ? b.detail : b.detail?.[0]?.msg || 'Request failed');
  }
  return res.status === 204 ? null : res.json();
}
export const api = {
  get: (p, params) => request('GET', p, { params }),
  post: (p, data) => request('POST', p, { data }),
  put: (p, data) => request('PUT', p, { data }),
  patch: (p, data) => request('PATCH', p, { data }),
};
