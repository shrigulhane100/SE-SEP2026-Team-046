import { useState } from 'react';
import { Bell, CheckCheck } from 'lucide-react';
import { Button, Card, Tabs } from '../../components/ui';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { notificationService } from '../../services/notificationService';
import { ago } from '../../lib/utils';

export default function Notifications() {
  const q = useAsync(notificationService.list, []); const [tab, setTab] = useState('all');
  return (
    <>
      <PageHeader title="Notifications" sub="Updates on requests, mentoring and your account." actions={<Button variant="outline" size="sm" onClick={async () => { await notificationService.readAll(); q.reload(); }}><CheckCheck size={15} />Mark all read</Button>} />
      <Load q={q} rows={4} className="h-14">{({ items, unread }) => { const list = tab === 'unread' ? items.filter((n) => !n.is_read) : items; return (<>
        <Tabs tabs={[{ id: 'all', label: 'All', count: items.length }, { id: 'unread', label: 'Unread', count: unread }]} value={tab} onChange={setTab} />
        <div className="mt-4">{list.length ? <Card className="!p-0 divide-y">{list.map((n) => <button key={n.id} onClick={async () => { if (!n.is_read) { await notificationService.read(n.id); q.reload(); } }} className={`w-full text-left px-5 py-4 flex gap-3 items-start ${n.is_read ? '' : 'bg-pale/40'}`}><span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${n.is_read ? 'bg-gray-300' : 'bg-accent'}`} /><span className="flex-1 text-sm">{n.message}</span><span className="text-xs text-gray-400 whitespace-nowrap">{ago(n.created_at)}</span></button>)}</Card> : <EmptyState icon={Bell} title="You're all caught up" />}</div></>); }}</Load>
    </>
  );
}
