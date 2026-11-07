import { forwardRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Loader2 } from 'lucide-react';
import { cn, label } from '../../lib/utils';

export const Button = ({ variant = 'primary', size = 'md', loading, className, children, disabled, ...p }) => {
  const v = { primary: 'bg-brand text-white hover:bg-indigo2', accent: 'bg-accent text-white hover:opacity-90', outline: 'border border-brand/40 text-brand hover:bg-pale', ghost: 'text-indigo2 hover:bg-pale', success: 'bg-emerald-600 text-white hover:bg-emerald-700', danger: 'bg-red-600 text-white hover:bg-red-700', dangerOutline: 'border border-red-300 text-red-700 hover:bg-red-50' }[variant];
  const s = { sm: 'h-9 px-3 text-sm', md: 'h-11 px-4 text-sm', lg: 'h-12 px-6 text-base' }[size];
  return <button type="button" disabled={disabled || loading} className={cn('inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lav', v, s, className)} {...p}>{loading && <Loader2 size={16} className="animate-spin" />}{children}</button>;
};
export const Card = ({ className, children, ...p }) => <div className={cn('bg-white rounded-card border border-black/5 shadow-soft p-5', className)} {...p}>{children}</div>;
export const Field = ({ label: l, error, hint, children, className }) => (
  <label className={cn('block', className)}>
    {l && <span className="block text-sm font-medium mb-1.5">{l}</span>}
    {children}
    {hint && !error && <span className="block text-xs text-gray-500 mt-1">{hint}</span>}
    {error && <span role="alert" className="block text-xs text-red-600 mt-1">{error}</span>}
  </label>
);
export const Input = forwardRef(({ className, ...p }, ref) => <input ref={ref} className={cn('field', className)} {...p} />);
export const Textarea = forwardRef(({ className, ...p }, ref) => <textarea ref={ref} className={cn('field', className)} {...p} />);
export const Select = forwardRef(({ className, children, ...p }, ref) => <select ref={ref} className={cn('field pr-8', className)} {...p}>{children}</select>);
export const Skeleton = ({ className }) => <div className={cn('animate-pulse rounded-xl bg-gray-200/70', className)} />;
export const Progress = ({ value = 0, className }) => (
  <div className={cn('h-2 rounded-full bg-pale overflow-hidden', className)} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}><div className="h-full rounded-full bg-accent transition-all duration-500" style={{ width: `${value}%` }} /></div>
);
export const Tag = ({ children, className }) => <span className={cn('inline-block px-2.5 py-1 rounded-full bg-pale text-brand text-xs font-medium', className)}>{children}</span>;
const hues = ['#8274D8', '#397F78', '#435A79', '#E7A17C', '#6558B8'];
export const Avatar = ({ name = '?', size = 44, className }) => {
  const i = [...name].reduce((s, c) => s + c.charCodeAt(0), 0) % hues.length;
  return <div className={cn('rounded-full text-white font-head font-bold flex items-center justify-center shrink-0', className)} style={{ width: size, height: size, background: hues[i], fontSize: size / 2.6 }} aria-hidden>{name.split(' ').filter((w) => !/^dr\.?$/i.test(w)).slice(0, 2).map((w) => w[0]).join('')}</div>;
};
export const Switch = ({ checked, onChange, label: l }) => (
  <button type="button" role="switch" aria-checked={checked} aria-label={l} onClick={() => onChange(!checked)} className={cn('w-11 h-6 rounded-full transition relative shrink-0', checked ? 'bg-accent' : 'bg-gray-300')}>
    <span className={cn('absolute top-0.5 w-5 h-5 rounded-full bg-white transition-all', checked ? 'left-[22px]' : 'left-0.5')} />
  </button>
);
export const Tabs = ({ tabs, value, onChange }) => (
  <div className="flex gap-1 p-1 bg-white rounded-xl border border-black/5 w-fit max-w-full overflow-x-auto" role="tablist">
    {tabs.map((t) => (
      <button key={t.id} role="tab" aria-selected={value === t.id} onClick={() => onChange(t.id)} className={cn('px-3.5 h-9 rounded-lg text-sm font-medium whitespace-nowrap transition', value === t.id ? 'bg-accent text-white' : 'text-gray-600 hover:bg-pale')}>
        {t.label}{t.count !== undefined && <span className={cn('ml-1.5 text-xs', value === t.id ? 'text-white/80' : 'text-gray-400')}>{t.count}</span>}
      </button>
    ))}
  </div>
);
export function Dialog({ open, onClose, title, children, wide }) {
  useEffect(() => { if (!open) return; const h = (e) => e.key === 'Escape' && onClose(); document.addEventListener('keydown', h); return () => document.removeEventListener('keydown', h); }, [open, onClose]);
  if (!open) return null;
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-0 bg-indigo2/40 backdrop-blur-sm" onClick={onClose} />
      <div className={cn('relative bg-white w-full rounded-t-section sm:rounded-section shadow-2xl max-h-[92vh] overflow-y-auto p-6', wide ? 'sm:max-w-2xl' : 'sm:max-w-lg')}>
        <div className="flex items-start justify-between gap-4 mb-4"><h2 className="text-xl font-bold">{title}</h2><button onClick={onClose} aria-label="Close" className="p-1 rounded-lg hover:bg-pale"><X size={20} /></button></div>
        {children}
      </div>
    </div>, document.body);
}
export const ConfirmationDialog = ({ open, onClose, onConfirm, title, text, confirmLabel = 'Confirm', danger, loading, children }) => (
  <Dialog open={open} onClose={onClose} title={title}>
    <p className="text-gray-600 mb-4">{text}</p>{children}
    <div className="flex justify-end gap-2 mt-5"><Button variant="ghost" onClick={onClose}>Cancel</Button><Button variant={danger ? 'danger' : 'primary'} loading={loading} onClick={onConfirm}>{confirmLabel}</Button></div>
  </Dialog>
);
export { label, cn };
