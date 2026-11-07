import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button, Card, Input } from '../../components/ui';
import { StatusBadge } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { adminService } from '../../services/adminService';
import { act } from '../../lib/utils';

export default function Guidance() {
  const q = useAsync(adminService.areas, []); const [name, setName] = useState('');
  return (
    <>
      <PageHeader title="Guidance areas" sub="Shared categories used by students (needs) and mentors (offers). Deactivating hides an area from new selections." />
      <Card className="mb-5"><form className="flex gap-2 max-w-md" onSubmit={async (e) => { e.preventDefault(); if (name.trim() && await act(() => adminService.addArea(name), 'Guidance area added')) { setName(''); q.reload(); } }}><Input placeholder="New guidance area" value={name} onChange={(e) => setName(e.target.value)} aria-label="New guidance area" /><Button type="submit"><Plus size={16} />Add</Button></form></Card>
      <Load q={q} rows={3} className="h-14">{(list) => <Card className="!p-0 divide-y">{list.map((a) => <div key={a.id} className="px-5 py-3 flex flex-wrap items-center justify-between gap-3"><div><div className="font-semibold">{a.name}</div><div className="text-xs text-gray-500">{a.mentors} mentors · {a.requests} requests</div></div><div className="flex items-center gap-3"><StatusBadge status={a.is_active ? 'ACTIVE' : 'INACTIVE'} /><Button size="sm" variant="outline" onClick={async () => { if (await act(() => adminService.setAreaActive(a.id, !a.is_active), 'Updated')) q.reload(); }}>{a.is_active ? 'Deactivate' : 'Activate'}</Button></div></div>)}</Card>}</Load>
    </>
  );
}
