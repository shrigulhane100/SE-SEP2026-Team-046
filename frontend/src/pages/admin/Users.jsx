import { useState } from 'react';
import { Search } from 'lucide-react';
import { Avatar, Button, Card, ConfirmationDialog, Input, Select } from '../../components/ui';
import { StatusBadge } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useDebounce } from '../../hooks/useDebounce';
import { useAuth } from '../../hooks/useAuth';
import { adminService } from '../../services/adminService';
import { act, fmtDate, label } from '../../lib/utils';

export default function Users() {
  const { user: me } = useAuth(); const [s, setS] = useState(''); const [role, setRole] = useState(''); const d = useDebounce(s); const [t, setT] = useState(null);
  const q = useAsync(() => adminService.users({ q: d, role }), [d, role]);
  return (
    <>
      <PageHeader title="User management" sub="View, search and activate or deactivate accounts. Deactivation keeps history intact." />
      <div className="flex flex-wrap gap-3 mb-5"><div className="relative flex-1 min-w-56 max-w-md"><Search size={16} className="absolute left-3 top-3.5 text-gray-400" /><Input className="pl-9" placeholder="Search name or email" value={s} onChange={(e) => setS(e.target.value)} aria-label="Search users" /></div><Select className="!w-44" value={role} onChange={(e) => setRole(e.target.value)} aria-label="Role"><option value="">All roles</option><option value="STUDENT">Students</option><option value="MENTOR">Mentors</option><option value="ADMIN">Admins</option></Select></div>
      <Load q={q} rows={4} className="h-14">{(list) => list.length ? <Card className="!p-0 overflow-x-auto"><table className="w-full text-sm min-w-[680px]"><thead className="text-left text-gray-500 border-b"><tr>{['User', 'Role', 'Joined', 'Status', ''].map((h) => <th key={h} className="px-5 py-3 font-medium">{h}</th>)}</tr></thead><tbody>{list.map((u) => <tr key={u.id} className="border-b last:border-0"><td className="px-5 py-3"><div className="flex items-center gap-3"><Avatar name={u.name} size={34} /><div><div className="font-semibold">{u.name}</div><div className="text-xs text-gray-500">{u.email}</div></div></div></td><td className="px-5 py-3">{label(u.role)}{u.role === 'MENTOR' && <div className="mt-1"><StatusBadge status={u.verification_status} /></div>}</td><td className="px-5 py-3 whitespace-nowrap">{fmtDate(u.created_at)}</td><td className="px-5 py-3"><StatusBadge status={u.is_active ? 'ACTIVE' : 'INACTIVE'} /></td><td className="px-5 py-3 text-right">{u.id !== me.id && <Button size="sm" variant={u.is_active ? 'dangerOutline' : 'outline'} onClick={() => setT(u)}>{u.is_active ? 'Deactivate' : 'Activate'}</Button>}</td></tr>)}</tbody></table></Card> : <EmptyState title="No users match" />}</Load>
      <ConfirmationDialog open={!!t} onClose={() => setT(null)} danger={t?.is_active} title={`${t?.is_active ? 'Deactivate' : 'Activate'} ${t?.name}?`} text={t?.is_active ? 'They will no longer be able to log in. Their history is kept.' : 'They will be able to log in again.'} confirmLabel={t?.is_active ? 'Deactivate' : 'Activate'} onConfirm={async () => { if (await act(() => adminService.setActive(t.id, !t.is_active), 'Account updated')) { setT(null); q.reload(); } }} />
    </>
  );
}
