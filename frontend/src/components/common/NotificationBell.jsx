import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { notificationService } from '../../services/notificationService';
import { useAsync } from '../../hooks/useAsync';
import { ago } from '../../lib/utils';

export default function NotificationBell({ role }) {
  const [open, setOpen] = useState(false); const ref = useRef(); const loc = useLocation();
  const q = useAsync(notificationService.list, []);
  useEffect(() => { const t = setInterval(q.reload, 20000); return () => clearInterval(t); }, [q.reload]);
  useEffect(() => { q.reload(); setOpen(false); }, [loc.pathname]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const h = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false); document.addEventListener('mousedown', h); return () => document.removeEventListener('mousedown', h); }, []);
  const items = q.data?.items.slice(0, 5) || []; const unread = q.data?.unread || 0;
  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(!open)} aria-label={`Notifications${unread ? `, ${unread} unread` : ''}`} className="relative p-2 rounded-xl hover:bg-pale"><Bell size={20} />{unread > 0 && <span className="absolute top-0.5 right-0.5 min-w-4 h-4 px-1 bg-peach text-white text-[10px] font-bold rounded-full flex items-center justify-center">{unread}</span>}</button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 max-w-[85vw] bg-white rounded-card shadow-2xl border border-black/5 z-40">
          <div className="flex items-center justify-between px-4 py-3 border-b"><b className="text-sm">Notifications</b>{unread > 0 && <button className="text-xs text-brand font-semibold" onClick={async () => { await notificationService.readAll(); q.reload(); }}>Mark all read</button>}</div>
          {items.length === 0 ? <p className="p-4 text-sm text-gray-500">You're all caught up.</p> : items.map((n) => (
            <div key={n.id} className={`px-4 py-3 text-sm border-b last:border-0 ${n.is_read ? '' : 'bg-pale/50'}`}>{n.message}<div className="text-xs text-gray-400 mt-0.5">{ago(n.created_at)}</div></div>))}
          <Link to={`/${role.toLowerCase()}/notifications`} className="block text-center text-sm font-semibold text-brand py-3">View all</Link>
        </div>
      )}
    </div>
  );
}
