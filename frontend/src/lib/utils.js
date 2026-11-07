import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { formatDistanceToNow, format } from 'date-fns';
import { toast } from 'sonner';
export const cn = (...a) => twMerge(clsx(a));
export const ago = (iso) => (iso ? formatDistanceToNow(new Date(iso), { addSuffix: true }) : '—');
export const fmtDate = (iso) => (iso ? format(new Date(iso), 'd MMM yyyy') : '—');
export const label = (s = '') => s.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
export const csv = (s = '') => s.split(',').map((x) => x.trim()).filter(Boolean);
export const greeting = () => { const h = new Date().getHours(); return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'; };
// Run an API call; toast on success/failure; resolves to undefined on failure.
export async function act(fn, ok) { try { const r = await fn(); if (ok) toast.success(ok); return r ?? true; } catch (e) { toast.error(e.message || 'Something went wrong'); return undefined; } }
