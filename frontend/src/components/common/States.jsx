import { AlertTriangle, Inbox } from 'lucide-react';
import { Button, Card, Skeleton } from '../ui';
export const EmptyState = ({ icon: Icon = Inbox, title, text, action }) => (
  <div className="text-center py-12 px-4 border border-dashed border-gray-300 rounded-card bg-white/50"><Icon className="mx-auto text-lav mb-3" size={32} /><div className="font-head font-bold">{title}</div>{text && <p className="text-sm text-gray-500 mt-1 max-w-sm mx-auto">{text}</p>}{action && <div className="mt-4">{action}</div>}</div>
);
export const ErrorState = ({ message, onRetry }) => (
  <Card className="text-center py-10"><AlertTriangle className="mx-auto text-red-500 mb-2" /><div className="font-semibold">Something went wrong</div><p className="text-sm text-gray-500 mt-1">{message}</p>{onRetry && <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>Try again</Button>}</Card>
);
export const LoadingState = ({ rows = 3, className = 'h-28' }) => <div className="grid gap-4" aria-busy="true" aria-label="Loading">{Array.from({ length: rows }).map((_, i) => <Skeleton key={i} className={className} />)}</div>;
// Render-prop wrapper for a useAsync() result.
export const Load = ({ q, rows, className, children }) => q.loading && !q.data ? <LoadingState rows={rows} className={className} /> : q.error ? <ErrorState message={q.error} onRetry={q.retry} /> : children(q.data);
