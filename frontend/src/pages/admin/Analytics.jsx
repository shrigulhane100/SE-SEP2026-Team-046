import { useState } from 'react';
import { Percent, Clock, Send, Users } from 'lucide-react';
import { StatCard, StatsGrid } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { Tabs } from '../../components/ui';
import { Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { adminService } from '../../services/adminService';
import { ChartCard, HBar, RegistrationsChart, StatusDonut } from './charts';

export default function Analytics() {
  const [days, setDays] = useState(''); const q = useAsync(() => adminService.stats(days), [days]);
  return (
    <>
      <PageHeader title="Reports & analytics" sub="Programme-level aggregates. No private notes or conversations." actions={<Tabs value={days} onChange={setDays} tabs={[{ id: '7', label: '7 days' }, { id: '30', label: '30 days' }, { id: '90', label: '90 days' }, { id: '', label: 'All time' }]} />} />
      <Load q={q} rows={4}>{(s) => (
        <div className="grid gap-6">
          <StatsGrid cols={4}><StatCard label="Requests in period" value={s.totals.total_requests} icon={Send} /><StatCard label="Acceptance rate" value={`${s.acceptance_rate}%`} icon={Percent} /><StatCard label="Avg. response time" value={s.avg_response_hours === null ? '—' : `${s.avg_response_hours}h`} icon={Clock} /><StatCard label="Active relationships" value={s.totals.active_relationships} icon={Users} /></StatsGrid>
          <div className="grid lg:grid-cols-2 gap-4">
            <ChartCard title="Request outcomes"><StatusDonut data={s.request_status} /></ChartCard>
            <ChartCard title="Demand by guidance area"><HBar data={s.demand} /></ChartCard>
            <ChartCard title="Registrations by month"><RegistrationsChart data={s.registrations} /></ChartCard>
            <ChartCard title="Mentors by type"><HBar data={s.mentor_types} color="#397F78" /></ChartCard>
          </div>
          <p className="text-sm text-gray-500">Participation: {s.participation.students_with_request} students have sent requests; {s.participation.mentors_with_mentee} mentors currently have mentees.</p>
        </div>)}</Load>
    </>
  );
}
