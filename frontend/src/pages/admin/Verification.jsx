import { Check, X, ShieldCheck } from 'lucide-react';
import { Button, Card } from '../../components/ui';
import { ExpertiseTags, ProfileHeader, StatusBadge } from '../../components/common/Cards';
import { PageHeader, Section } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { adminService } from '../../services/adminService';
import { act, fmtDate } from '../../lib/utils';

export default function Verification() {
  const q = useAsync(adminService.verifications, []);
  const decide = async (m, ok) => { if (await act(() => adminService.verify(m.id, ok), ok ? `${m.name} verified` : `${m.name} rejected`)) q.reload(); };
  return (
    <>
      <PageHeader title="Mentor verification" sub="Review alumni, industry and faculty mentors before they appear to students." />
      <Load q={q} rows={2} className="h-40">{(list) => { const pend = list.filter((m) => m.verification_status === 'PENDING'); const rest = list.filter((m) => m.verification_status !== 'PENDING'); return (
        <div className="grid gap-8">
          <Section title={`Awaiting review (${pend.length})`}>{pend.length ? <div className="grid lg:grid-cols-2 gap-4">{pend.map((m) => <Card key={m.id} className="grid gap-3"><ProfileHeader name={m.name} sub={`${m.current_role || 'Role not set'} · ${m.organisation || 'Organisation not set'}`} /><div className="text-xs text-gray-500">{m.email} · registered {fmtDate(m.registered_at)} · {m.mentor_type} · {m.experience_years} yrs</div><ExpertiseTags items={[...m.areas, ...m.skills]} max={5} /><p className="text-sm text-gray-600">{m.bio || 'No biography yet.'}</p><div className="flex gap-2"><Button size="sm" variant="success" onClick={() => decide(m, true)}><Check size={15} />Verify</Button><Button size="sm" variant="dangerOutline" onClick={() => decide(m, false)}><X size={15} />Reject</Button></div></Card>)}</div> : <EmptyState icon={ShieldCheck} title="No mentors waiting" text="New mentor registrations will appear here." />}</Section>
          <Section title="Reviewed mentors"><Card className="!p-0 divide-y">{rest.map((m) => <div key={m.id} className="px-5 py-3 flex items-center justify-between gap-3 text-sm"><div><b>{m.name}</b><div className="text-xs text-gray-500">{m.current_role} · {m.mentor_type}</div></div><div className="flex items-center gap-2"><StatusBadge status={m.verification_status} />{m.verification_status === 'VERIFIED' ? <Button size="sm" variant="ghost" onClick={() => decide(m, false)}>Revoke</Button> : <Button size="sm" variant="ghost" onClick={() => decide(m, true)}>Verify</Button>}</div></div>)}</Card></Section>
        </div>); }}</Load>
    </>
  );
}
