import { Star } from 'lucide-react';
import { Card } from '../../components/ui';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { relationshipService } from '../../services/relationshipService';
import { ago } from '../../lib/utils';

export default function MentorFeedback() {
  const q = useAsync(relationshipService.myFeedback, []);
  return (<><PageHeader title="Feedback" sub="What your mentees have shared." /><Load q={q} rows={2} className="h-24">{({ items, average }) => items.length ? <div className="grid gap-4 max-w-3xl"><Card className="flex items-center gap-4"><Star className="text-amber-400" fill="currentColor" size={32} /><div><div className="text-3xl font-head font-extrabold">{average} <span className="text-base font-normal text-gray-500">/ 5</span></div><div className="text-sm text-gray-500">{items.length} review{items.length > 1 ? 's' : ''}</div></div></Card>{items.map((f) => <Card key={f.id}><div className="flex justify-between"><b>{f.given_by_name}</b><span className="text-amber-500">{'★'.repeat(f.rating)}{'☆'.repeat(5 - f.rating)}</span></div><div className="text-xs text-gray-400 mb-2">{f.area} · {ago(f.created_at)}</div><p className="text-sm text-gray-700">{f.comments || 'No comment.'}</p></Card>)}</div> : <EmptyState icon={Star} title="No feedback yet" text="Feedback appears after mentees rate their mentoring." />}</Load></>);
}
