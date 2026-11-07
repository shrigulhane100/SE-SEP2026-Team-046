import { Link } from 'react-router-dom';
import { ListChecks } from 'lucide-react';
import { Card, Progress } from '../../components/ui';
import { StatusBadge } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { relationshipService } from '../../services/relationshipService';
import { fmtDate, label } from '../../lib/utils';

export default function GoalsOverview({ role }) {
  const q = useAsync(relationshipService.list, []); const S = role === 'STUDENT'; const base = S ? '/student/mentoring' : '/mentor/mentees';
  return (
    <>
      <PageHeader title={S ? 'Goals & progress' : 'Goals & activities'} sub={S ? 'Track objectives across all your mentoring.' : 'Goals and recent activity across your mentees.'} />
      <Load q={q} rows={2} className="h-40">{(list) => {
        const goals = list.flatMap((r) => r.goals); const done = goals.filter((g) => g.status === 'DONE').length; const pct = goals.length ? Math.round((100 * done) / goals.length) : 0;
        if (!list.length) return <EmptyState icon={ListChecks} title="Nothing to track yet" text="Goals appear once a mentoring relationship starts." />;
        return (<div className="grid gap-5">
          <Card><div className="flex justify-between mb-2"><b>Overall progress</b><span className="text-sm text-gray-500">{done} of {goals.length} goals done</span></div><Progress value={pct} /></Card>
          {list.map((r) => <Card key={r.id}><div className="flex flex-wrap justify-between gap-2 mb-3"><Link to={`${base}/${r.id}`} className="font-bold text-brand">{S ? r.mentor.name : r.student.name} <span className="font-normal text-gray-500">· {r.area}</span></Link><StatusBadge status={r.status} /></div><Progress value={r.progress} className="mb-3" />
            <div className="grid md:grid-cols-2 gap-4"><ul className="grid gap-1.5 text-sm content-start">{r.goals.length ? r.goals.map((g) => <li key={g.id} className="flex justify-between gap-2"><span className={g.status === 'DONE' ? 'line-through text-gray-400' : ''}>{g.title}</span><StatusBadge status={g.status} /></li>) : <li className="text-gray-500">No goals yet.</li>}</ul>
              <ul className="grid gap-1.5 text-sm content-start">{r.activities.slice(0, 3).map((a) => <li key={a.id} className="text-gray-600"><b>{label(a.activity_type)}</b> · {fmtDate(a.activity_date)}<div className="text-xs text-gray-400 truncate">{a.notes}</div></li>)}{!r.activities.length && <li className="text-gray-500">No activities logged.</li>}</ul></div></Card>)}
        </div>);
      }}</Load>
    </>
  );
}
