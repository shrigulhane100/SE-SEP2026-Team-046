import { Users, GraduationCap, Link2, Send, Percent, ShieldCheck } from 'lucide-react';
import { StatCard, StatsGrid, StatusBadge } from '../../components/common/Cards';
import { Card } from '../../components/ui';
import { PageHeader } from '../../components/common/PageHeader';
import { Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { adminService } from '../../services/adminService';
import { ChartCard, HBar, RegistrationsChart, StatusDonut } from './charts';
import { ago } from '../../lib/utils';

export default function AdminDashboard() {
  const q = useAsync(async () => ({ s: await adminService.stats(), a: await adminService.activity() }), []);
  return (
    <>
      <PageHeader title="Programme overview" sub="Aggregate participation across Rock Starz. Private mentoring content is never shown here." />
      <Load q={q} rows={4}>{({ s, a }) => (
        <div className="grid gap-6">
          <StatsGrid cols={3}><StatCard label="Total students" value={s.totals.students} icon={GraduationCap} to="/admin/users" /><StatCard label="Total mentors" value={s.totals.mentors} icon={Users} to="/admin/users" /><StatCard label="Active relationships" value={s.totals.active_relationships} icon={Link2} to="/admin/relationships" /><StatCard label="Pending requests" value={s.totals.pending_requests} icon={Send} to="/admin/requests" /><StatCard label="Acceptance rate" value={`${s.acceptance_rate}%`} icon={Percent} hint="Accepted ÷ (accepted + rejected + expired)" /><StatCard label="Awaiting verification" value={s.totals.pending_verifications} icon={ShieldCheck} to="/admin/verification" /></StatsGrid>
          <div className="grid lg:grid-cols-3 gap-4">
            <ChartCard title="Registrations" sub="Monthly trend" className="lg:col-span-2"><RegistrationsChart data={s.registrations} /></ChartCard>
            <ChartCard title="Request status" sub="All requests"><StatusDonut data={s.request_status} /></ChartCard>
            <ChartCard title="Popular guidance areas" sub="Requests per area" className="lg:col-span-2"><HBar data={s.demand} /></ChartCard>
            <Card className="!p-0"><h3 className="font-bold p-5 pb-2">Recent activity</h3><ul className="divide-y">{a.map((e, i) => <li key={i} className="px-5 py-3 text-sm flex justify-between gap-2"><div><div>{e.text}</div><div className="text-xs text-gray-400">{ago(e.at)}</div></div><StatusBadge status={e.status} /></li>)}</ul></Card>
          </div>
        </div>)}</Load>
    </>
  );
}
