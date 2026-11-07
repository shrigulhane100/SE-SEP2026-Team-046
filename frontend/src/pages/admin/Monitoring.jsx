import { useState } from 'react';
import { Search } from 'lucide-react';
import { Button, Card, Input, Progress, Select, Tabs } from '../../components/ui';
import { StatusBadge } from '../../components/common/Cards';
import { PageHeader, Section } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useDebounce } from '../../hooks/useDebounce';
import { adminService } from '../../services/adminService';
import { act, fmtDate, label } from '../../lib/utils';

const Table = ({ heads, children }) => <Card className="!p-0 overflow-x-auto"><table className="w-full text-sm min-w-[640px]"><thead className="text-left text-gray-500 border-b"><tr>{heads.map((h) => <th key={h} className="px-5 py-3 font-medium">{h}</th>)}</tr></thead><tbody>{children}</tbody></table></Card>;
export function AdminRequests() {
  const [s, setS] = useState(''); const [status, setStatus] = useState(''); const d = useDebounce(s);
  const q = useAsync(() => adminService.requests({ q: d, status }), [d, status]);
  return (
    <>
      <PageHeader title="Mentoring requests" sub="Request metadata only. Message content is private to students and mentors." />
      <div className="flex flex-wrap gap-3 mb-5"><div className="relative flex-1 min-w-56 max-w-md"><Search size={16} className="absolute left-3 top-3.5 text-gray-400" /><Input className="pl-9" placeholder="Search student or mentor" value={s} onChange={(e) => setS(e.target.value)} aria-label="Search requests" /></div><Select className="!w-44" value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status"><option value="">All statuses</option>{['PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CANCELLED'].map((x) => <option key={x} value={x}>{label(x)}</option>)}</Select></div>
      <Load q={q} rows={4} className="h-14">{(list) => list.length ? <Table heads={['Request', 'Student', 'Mentor', 'Area', 'Sent', 'Status']}>{list.map((r) => <tr key={r.id} className="border-b last:border-0"><td className="px-5 py-3 mono">#RS-{String(r.id).padStart(5, '0')}</td><td className="px-5 py-3">{r.student.name}</td><td className="px-5 py-3">{r.mentor.name}</td><td className="px-5 py-3">{r.area}<div className="text-xs text-gray-500">{label(r.type)}</div></td><td className="px-5 py-3 whitespace-nowrap">{fmtDate(r.created_at)}</td><td className="px-5 py-3"><StatusBadge status={r.status} /></td></tr>)}</Table> : <EmptyState title="No requests match" />}</Load>
    </>
  );
}
export function AdminRelationships() {
  const [tab, setTab] = useState('');
  const q = useAsync(() => adminService.relationships({ status: tab }), [tab]); const rep = useAsync(adminService.reports, []);
  return (
    <>
      <PageHeader title="Active relationships" sub="Monitor mentoring health. Notes and goal text stay private." />
      <Tabs value={tab} onChange={setTab} tabs={[{ id: '', label: 'All' }, ...['ACTIVE', 'PAUSED', 'COMPLETED', 'CLOSED'].map((x) => ({ id: x, label: label(x) }))]} />
      <div className="mt-4 mb-8"><Load q={q} rows={3} className="h-14">{(list) => list.length ? <Table heads={['Student', 'Mentor', 'Area', 'Started', 'Goals', 'Activities', 'Status']}>{list.map((r) => <tr key={r.id} className="border-b last:border-0"><td className="px-5 py-3">{r.student.name}</td><td className="px-5 py-3">{r.mentor.name}</td><td className="px-5 py-3">{r.area}</td><td className="px-5 py-3 whitespace-nowrap">{fmtDate(r.started_at)}</td><td className="px-5 py-3 w-40"><Progress value={r.progress} /><div className="text-xs text-gray-500 mt-1">{r.progress}% of {r.goals_total}</div></td><td className="px-5 py-3">{r.activities_count}</td><td className="px-5 py-3"><StatusBadge status={r.status} /></td></tr>)}</Table> : <EmptyState title="No relationships" />}</Load></div>
      <Section title="Advice reports"><Load q={rep} rows={1} className="h-20">{(list) => list.length ? <div className="grid gap-3">{list.map((r) => <Card key={r.id} className="flex flex-wrap justify-between items-start gap-3"><div className="text-sm"><b>{r.student}</b> reported advice from <b>{r.mentor}</b><p className="text-gray-600 mt-1">{r.reason}</p><div className="text-xs text-gray-400 mt-1">{fmtDate(r.created_at)}</div></div><div className="flex items-center gap-2"><StatusBadge status={r.status} />{r.status === 'OPEN' && <Button size="sm" variant="outline" onClick={async () => { if (await act(() => adminService.reviewReport(r.id), 'Marked reviewed')) rep.reload(); }}>Mark reviewed</Button>}</div></Card>)}</div> : <EmptyState title="No reports" />}</Load></Section>
    </>
  );
}
