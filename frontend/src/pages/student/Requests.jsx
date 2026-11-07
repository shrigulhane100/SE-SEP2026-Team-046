import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Send } from 'lucide-react';
import { Button, Card, ConfirmationDialog, Dialog, Tabs } from '../../components/ui';
import { StatusBadge } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { requestService } from '../../services/requestService';
import { act, fmtDate, label } from '../../lib/utils';

export default function MyRequests() {
  const q = useAsync(requestService.list, []); const [tab, setTab] = useState('ALL'); const [view, setView] = useState(null); const [cancel, setCancel] = useState(null);
  return (
    <>
      <PageHeader title="My requests" sub="Track every mentoring request you've sent." />
      <Load q={q} rows={3} className="h-16">{(all) => {
        const tabs = ['ALL', 'PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CANCELLED'].map((t) => ({ id: t, label: t === 'ALL' ? 'All' : label(t), count: t === 'ALL' ? all.length : all.filter((r) => r.status === t).length }));
        const list = tab === 'ALL' ? all : all.filter((r) => r.status === tab);
        return (<>
          <Tabs tabs={tabs} value={tab} onChange={setTab} />
          <div className="mt-4">{list.length === 0 ? <EmptyState icon={Send} title="No requests here" action={<Link to="/student/mentors"><Button size="sm">Discover mentors</Button></Link>} /> : (
            <Card className="!p-0 overflow-x-auto"><table className="w-full text-sm min-w-[640px]"><thead className="text-left text-gray-500 border-b"><tr>{['Mentor', 'Guidance area', 'Sent', 'Status', ''].map((h) => <th key={h} className="px-5 py-3 font-medium">{h}</th>)}</tr></thead>
              <tbody>{list.map((r) => <tr key={r.id} className="border-b last:border-0"><td className="px-5 py-3"><div className="font-semibold">{r.mentor.name}</div><div className="text-xs text-gray-500">{r.mentor.current_role}</div></td><td className="px-5 py-3">{r.area}<div className="text-xs text-gray-500">{label(r.type)}</div></td><td className="px-5 py-3 whitespace-nowrap">{fmtDate(r.created_at)}{r.status === 'PENDING' && <div className="text-xs text-amber-700">expires in {r.hours_left}h</div>}</td><td className="px-5 py-3"><StatusBadge status={r.status} /></td>
                <td className="px-5 py-3 text-right whitespace-nowrap"><Button size="sm" variant="ghost" onClick={() => setView(r)}>View</Button>{r.status === 'PENDING' && <Button size="sm" variant="dangerOutline" onClick={() => setCancel(r)}>Cancel</Button>}{r.status === 'ACCEPTED' && r.relationship_id && <Link to={`/student/mentoring/${r.relationship_id}`}><Button size="sm" variant="outline">Open</Button></Link>}{['EXPIRED', 'REJECTED'].includes(r.status) && <Link to="/student/mentors"><Button size="sm" variant="outline">Try another</Button></Link>}</td></tr>)}</tbody></table></Card>)}</div>
        </>);
      }}</Load>
      <Dialog open={!!view} onClose={() => setView(null)} title="Request details">{view && <div className="grid gap-3 text-sm"><div className="flex justify-between"><b>{view.mentor.name}</b><StatusBadge status={view.status} /></div><div><span className="text-gray-500">Area:</span> {view.area} · {label(view.type)}</div><div className="bg-ivory rounded-xl p-3">{view.message}</div>{view.objective && <div><span className="text-gray-500">Objective:</span> {view.objective}</div>}{view.reject_reason && <div className="bg-red-50 rounded-xl p-3"><b>Mentor's reason:</b> {view.reject_reason}</div>}{view.status === 'EXPIRED' && <div className="bg-gray-100 rounded-xl p-3">This request expired with no response. Try another mentor.</div>}<div className="mono text-gray-400">Request #RS-{String(view.id).padStart(5, '0')}</div></div>}</Dialog>
      <ConfirmationDialog open={!!cancel} onClose={() => setCancel(null)} title="Cancel this request?" text={`Your request to ${cancel?.mentor.name} will be withdrawn.`} confirmLabel="Cancel request" danger onConfirm={async () => { if (await act(() => requestService.cancel(cancel.id), 'Request cancelled')) { setCancel(null); q.reload(); } }} />
    </>
  );
}
