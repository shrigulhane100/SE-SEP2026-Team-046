import { Link } from 'react-router-dom';
import { Users, Inbox, Star, Gauge } from 'lucide-react';
import { Card, Progress } from '../../components/ui';
import { StatCard, StatsGrid, StatusBadge } from '../../components/common/Cards';
import { PageHeader, Section } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useAuth } from '../../hooks/useAuth';
import { profileService } from '../../services/profileService';
import { ago, fmtDate, greeting, label } from '../../lib/utils';

export default function MentorDashboard() {
  const { user } = useAuth(); const q = useAsync(profileService.dashboard, []);
  return (
    <>
      <PageHeader title={`${greeting()}, ${user.name.split(' ')[0]}!`} sub="Your mentoring overview." />
      <Load q={q} rows={4}>{(d) => (
        <div className="grid gap-6">
          <StatsGrid cols={4}><StatCard label="Active mentees" value={d.stats.active_mentees} icon={Users} to="/mentor/mentees" /><StatCard label="Pending requests" value={d.stats.pending_requests} icon={Inbox} to="/mentor/requests" /><StatCard label="Average rating" value={d.stats.average_rating ?? '—'} icon={Star} to="/mentor/feedback" /><StatCard label="Accepting requests" value={d.stats.is_accepting ? 'Yes' : 'No'} icon={Gauge} to="/mentor/profile" /></StatsGrid>
          <div className="grid lg:grid-cols-3 gap-4">
            <Card><div className="text-xs font-semibold text-gray-500 tracking-wide">MENTORING CAPACITY</div><div className="text-4xl font-head font-extrabold my-1">{d.stats.active_mentees} / {d.stats.max_mentees}</div><Progress value={(100 * d.stats.active_mentees) / d.stats.max_mentees} className="my-2" /><p className="text-xs text-gray-500">{d.stats.max_mentees - d.stats.active_mentees > 0 ? `${d.stats.max_mentees - d.stats.active_mentees} slot(s) available.` : 'At full capacity. New requests cannot be accepted.'}</p></Card>
            <Card className="lg:col-span-2"><div className="flex justify-between mb-3"><h2 className="font-bold">Request inbox</h2><Link to="/mentor/requests" className="text-sm text-brand font-semibold">Open inbox</Link></div>
              {d.inbox_preview.length ? <ul className="divide-y">{d.inbox_preview.map((r) => <li key={r.id} className="py-3 flex justify-between gap-3 text-sm"><div className="min-w-0"><b>{r.student.name}</b> · {r.area}<div className="text-gray-500 truncate">{r.message}</div></div><span className="text-xs text-amber-700 whitespace-nowrap">{r.hours_left}h left</span></li>)}</ul> : <p className="text-sm text-gray-500">No pending requests.</p>}</Card>
          </div>
          <div className="grid lg:grid-cols-2 gap-4">
            <Section title="Upcoming priorities"><Card className="!p-0 divide-y">{d.priorities.length ? d.priorities.map((g) => <Link key={g.id} to={`/mentor/mentees/${g.relationship_id}`} className="px-5 py-3 flex justify-between gap-3 text-sm hover:bg-pale/40"><span>{g.title}<span className="block text-xs text-gray-400">{g.student}</span></span><StatusBadge status={g.status} /></Link>) : <p className="p-5 text-sm text-gray-500">No open goals.</p>}</Card></Section>
            <Section title="Recent mentoring activities"><Card className="!p-0 divide-y">{d.recent_activities.length ? d.recent_activities.map((a) => <div key={a.id} className="px-5 py-3 text-sm"><b>{label(a.activity_type)}</b> with {a.student}<span className="block text-xs text-gray-400">{fmtDate(a.activity_date)} · {ago(a.created_at)}</span></div>) : <p className="p-5 text-sm text-gray-500">Nothing logged yet.</p>}</Card></Section>
          </div>
        </div>)}</Load>
    </>
  );
}
