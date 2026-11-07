import { Link } from 'react-router-dom';
import { Users, Send, CheckCircle2, Search, ArrowRight, Map } from 'lucide-react';
import { Card, Progress, Button } from '../../components/ui';
import { StatCard, StatsGrid, MentorCard, RelationshipCard } from '../../components/common/Cards';
import { PageHeader, Section } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useAuth } from '../../hooks/useAuth';
import { profileService } from '../../services/profileService';
import { ago, greeting } from '../../lib/utils';

export default function StudentDashboard() {
  const { user } = useAuth(); const q = useAsync(profileService.dashboard, []);
  return (
    <>
      <PageHeader title={`${greeting()}, ${user.name.split(' ')[0]}!`} sub="Here's your mentoring journey at a glance." />
      <Load q={q} rows={4}>{(d) => {
        const stage = d.profile_completion < 100 ? 0 : d.stats.active_mentors ? 3 : d.requests_total ? 2 : 1;
        return (
          <div className="grid gap-6">
            <StatsGrid><StatCard label="Active mentors" value={d.stats.active_mentors} icon={Users} to="/student/mentoring" /><StatCard label="Pending requests" value={d.stats.pending_requests} icon={Send} to="/student/requests" /><StatCard label="Goals completed" value={`${d.stats.goals_completed}/${d.stats.goals_total}`} icon={CheckCircle2} to="/student/goals" /></StatsGrid>
            <div className="grid lg:grid-cols-3 gap-4">
              <Card className="lg:col-span-2">
                <h2 className="font-bold mb-4 flex items-center gap-2"><Map size={18} className="text-accent" />Your mentoring journey</h2>
                <ol className="grid sm:grid-cols-4 gap-3">{['Complete profile', 'Discover mentors', 'Send requests', 'Start mentoring'].map((t, i) => <li key={t} className={`rounded-xl p-3 text-sm border ${i < stage ? 'bg-emerald-50 border-emerald-200' : i === stage ? 'bg-accent/10 border-accent' : 'bg-white'}`}><div className="mono text-gray-400">0{i + 1}</div><div className="font-semibold">{t}</div><div className="text-xs text-gray-500">{i < stage ? 'Done' : i === stage ? 'Current step' : 'Next'}</div></li>)}</ol>
              </Card>
              <Card><div className="text-sm text-gray-500">Profile completion</div><div className="text-4xl font-head font-extrabold my-1">{d.profile_completion}%</div><Progress value={d.profile_completion} />{d.profile_completion < 100 && <Link to="/student/profile" className="text-sm text-brand font-semibold mt-3 inline-block">Finish your profile</Link>}</Card>
            </div>
            <Card className="glass !bg-gradient-to-r from-pale to-white flex flex-wrap items-center justify-between gap-4">
              <div><div className="text-xs font-semibold text-accent uppercase">Suggested action</div><h3 className="text-lg font-bold">Explore mentors in {d.suggested_area}</h3><p className="text-sm text-gray-600">Find experienced professionals who can guide your next step.</p></div>
              <Link to="/student/mentors"><Button variant="accent"><Search size={16} />Discover mentors</Button></Link>
            </Card>
            <Section title="Current mentoring" action={<Link to="/student/mentoring" className="text-sm text-brand font-semibold">View all</Link>}>
              {d.relationships.length ? <div className="grid md:grid-cols-2 gap-4">{d.relationships.map((r) => <RelationshipCard key={r.id} rel={r} role="STUDENT" to={`/student/mentoring/${r.id}`} />)}</div> : <EmptyState title="No active mentoring yet" text="Send a request to a mentor to begin." action={<Link to="/student/mentors"><Button size="sm">Find a mentor</Button></Link>} />}
            </Section>
            <Section title="Recommended mentors" action={<Link to="/student/mentors" className="text-sm text-brand font-semibold inline-flex items-center gap-1">Discover more <ArrowRight size={14} /></Link>}>
              <div className="grid md:grid-cols-3 gap-4">{d.recommended.map((m) => <MentorCard key={m.id} m={m} />)}</div>
            </Section>
            <Section title="Recent activity"><Card className="divide-y !p-0">{d.recent_activity.length ? d.recent_activity.map((n) => <div key={n.id} className="px-5 py-3 text-sm flex justify-between gap-4"><span>{n.message}</span><span className="text-xs text-gray-400 whitespace-nowrap">{ago(n.created_at)}</span></div>) : <p className="p-5 text-sm text-gray-500">Nothing yet.</p>}</Card></Section>
          </div>);
      }}</Load>
    </>
  );
}
