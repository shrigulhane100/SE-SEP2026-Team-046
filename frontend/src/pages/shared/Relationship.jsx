import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Flag, Pause, Play, CheckCheck, XCircle, Plus, Star, Info } from 'lucide-react';
import { Avatar, Button, Card, ConfirmationDialog, Dialog, Input, Progress, Select, Textarea, cn } from '../../components/ui';
import { StatusBadge } from '../../components/common/Cards';
import { Load, EmptyState } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useAuth } from '../../hooks/useAuth';
import { relationshipService as svc } from '../../services/relationshipService';
import { act, ago, fmtDate, label } from '../../lib/utils';

const ACT = ['MEETING', 'RESUME_REVIEW', 'MOCK_INTERVIEW', 'CHECK_IN', 'OTHER'];
const NEXT = { TODO: 'IN_PROGRESS', IN_PROGRESS: 'DONE', DONE: 'TODO' };
const Stars = ({ value, onChange }) => <div className="flex gap-1" role="radiogroup" aria-label="Rating">{[1, 2, 3, 4, 5].map((n) => <button key={n} type="button" role="radio" aria-checked={value === n} aria-label={`${n} star${n > 1 ? 's' : ''}`} onClick={() => onChange?.(n)} className={n <= value ? 'text-amber-400' : 'text-gray-300'}><Star size={22} fill="currentColor" /></button>)}</div>;

export default function RelationshipPage() {
  const { id } = useParams(); const { user } = useAuth(); const role = user.role; const base = role === 'STUDENT' ? '/student/mentoring' : '/mentor/mentees';
  const q = useAsync(() => svc.get(id), [id]);
  const [goal, setGoal] = useState(''); const [a, setA] = useState({ activity_type: 'MEETING', notes: '', activity_date: new Date().toISOString().slice(0, 10) });
  const [confirm, setConfirm] = useState(null); const [report, setReport] = useState(false); const [reason, setReason] = useState('');
  const [fb, setFb] = useState({ rating: 0, comments: '' });
  useEffect(() => { const m = q.data?.feedback.find((f) => f.given_by === user.id); if (m) setFb({ rating: m.rating, comments: m.comments }); }, [q.data?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const run = async (fn, ok) => { if (await act(fn, ok)) q.reload(); };
  return (
    <>
      <Link to={base} className="inline-flex items-center gap-1 text-sm text-brand font-semibold mb-4"><ArrowLeft size={14} />Back</Link>
      <Load q={q} rows={2} className="h-64">{(r) => {
        const who = role === 'STUDENT' ? r.mentor : r.student; const open = ['ACTIVE', 'PAUSED'].includes(r.status); const mine = r.feedback.find((f) => f.given_by === user.id);
        return (
          <div className="grid gap-6">
            <Card className="flex flex-wrap items-center gap-4 justify-between">
              <div className="flex items-center gap-4"><Avatar name={who.name} size={60} /><div><h1 className="text-xl font-extrabold">{who.name}</h1><p className="text-sm text-gray-500">{role === 'STUDENT' ? `${who.current_role} · ${who.organisation}` : `${who.education} · ${who.roll_number}`}</p><div className="flex flex-wrap items-center gap-2 mt-2 text-xs"><StatusBadge status={r.status} /><span className="px-2.5 py-1 rounded-full bg-pale text-brand font-medium">{r.area}</span><span className="text-gray-500">{label(r.type)} · started {fmtDate(r.started_at)}</span></div></div></div>
              {open && <div className="flex flex-wrap gap-2">
                {r.status === 'ACTIVE' ? <Button variant="outline" size="sm" onClick={() => setConfirm({ s: 'PAUSED', t: 'Pause this mentoring?', x: 'Pausing keeps the relationship but marks it as on hold. You can resume any time.' })}><Pause size={15} />Pause</Button> : <Button variant="outline" size="sm" onClick={() => run(() => svc.setStatus(r.id, 'ACTIVE'), 'Mentoring resumed')}><Play size={15} />Resume</Button>}
                <Button variant="success" size="sm" onClick={() => setConfirm({ s: 'COMPLETED', t: 'Mark as completed?', x: 'This ends the mentoring. You can still give feedback afterwards.' })}><CheckCheck size={15} />Complete</Button>
                {role === 'MENTOR' && <Button variant="dangerOutline" size="sm" onClick={() => setConfirm({ s: 'CLOSED', t: 'Close this relationship?', x: 'Use this if mentoring cannot continue. It frees up your capacity.', d: true })}><XCircle size={15} />Close</Button>}
              </div>}
            </Card>
            <div className="grid lg:grid-cols-2 gap-6">
              <Card><div className="flex justify-between items-center mb-2"><h2 className="font-bold">Goals</h2><span className="text-sm text-gray-500">{r.progress}% complete</span></div><Progress value={r.progress} className="mb-4" />
                {r.goals.length === 0 && <p className="text-sm text-gray-500 mb-3">No goals yet. Add the first one together.</p>}
                <ul className="grid gap-2 mb-4">{r.goals.map((g) => <li key={g.id} className="flex items-center justify-between gap-3 p-3 rounded-xl bg-ivory"><div className="min-w-0"><div className={cn('text-sm font-medium', g.status === 'DONE' && 'line-through text-gray-400')}>{g.title}</div><div className="text-xs text-gray-400">by {g.created_by_name}</div></div><button disabled={!open} onClick={() => run(() => svc.setGoalStatus(g.id, NEXT[g.status]))} title="Click to change status" className="disabled:opacity-60"><StatusBadge status={g.status} /></button></li>)}</ul>
                {open && <form className="flex gap-2" onSubmit={async (e) => { e.preventDefault(); if (goal.trim() && await act(() => svc.addGoal(r.id, goal), 'Goal added')) { setGoal(''); q.reload(); } }}><Input placeholder="Add a goal" value={goal} onChange={(e) => setGoal(e.target.value)} aria-label="New goal" /><Button type="submit" variant="accent"><Plus size={16} />Add</Button></form>}
              </Card>
              <Card><h2 className="font-bold mb-4">Activity log</h2>
                {open && <form className="grid gap-2 mb-4 p-3 rounded-xl bg-ivory" onSubmit={async (e) => { e.preventDefault(); if (a.notes.trim().length < 3) return; if (await act(() => svc.addActivity(r.id, a), 'Activity logged')) { setA({ ...a, notes: '' }); q.reload(); } }}>
                  <div className="grid grid-cols-2 gap-2"><Select value={a.activity_type} onChange={(e) => setA({ ...a, activity_type: e.target.value })} aria-label="Activity type">{ACT.map((t) => <option key={t} value={t}>{label(t)}</option>)}</Select><Input type="date" value={a.activity_date} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setA({ ...a, activity_date: e.target.value })} aria-label="Date" /></div>
                  <Textarea className="!h-20" placeholder="Notes (visible to you and your counterpart only)" value={a.notes} onChange={(e) => setA({ ...a, notes: e.target.value })} /><Button type="submit" size="sm" variant="accent" className="justify-self-end">Log activity</Button></form>}
                {r.activities.length === 0 ? <EmptyState title="No activities yet" /> : <ol className="grid gap-3">{r.activities.map((x) => <li key={x.id} className="border-l-2 border-accent pl-3"><div className="text-sm font-semibold">{label(x.activity_type)} <span className="font-normal text-gray-400">· {fmtDate(x.activity_date)}</span></div><p className="text-sm text-gray-600">{x.notes}</p><div className="text-xs text-gray-400">{x.created_by_name} · {ago(x.created_at)}</div></li>)}</ol>}
              </Card>
            </div>
            <Card><h2 className="font-bold mb-1">Feedback</h2><p className="text-xs text-gray-500 mb-4 flex gap-1"><Info size={13} className="mt-0.5" />Ratings help programme insights. You can update yours any time.</p>
              <div className="grid md:grid-cols-2 gap-6"><div className="grid gap-3"><Stars value={fb.rating} onChange={(n) => setFb({ ...fb, rating: n })} /><Textarea className="!h-20" placeholder="Share a few words (optional)" value={fb.comments} onChange={(e) => setFb({ ...fb, comments: e.target.value })} /><div className="flex gap-2"><Button size="sm" disabled={!fb.rating} onClick={() => run(() => svc.feedback(r.id, fb), 'Feedback saved')}>{mine ? 'Update feedback' : 'Submit feedback'}</Button>{role === 'STUDENT' && <Button size="sm" variant="dangerOutline" onClick={() => setReport(true)}><Flag size={14} />Report advice</Button>}</div></div>
                <div className="grid gap-2 content-start">{r.feedback.length === 0 ? <p className="text-sm text-gray-500">No feedback yet.</p> : r.feedback.map((f) => <div key={f.id} className="p-3 rounded-xl bg-ivory text-sm"><div className="flex justify-between"><b>{f.given_by_name}</b><span className="text-amber-500">{'★'.repeat(f.rating)}</span></div>{f.comments && <p className="text-gray-600">{f.comments}</p>}</div>)}</div></div></Card>
            <ConfirmationDialog open={!!confirm} onClose={() => setConfirm(null)} title={confirm?.t} text={confirm?.x} danger={confirm?.d} confirmLabel="Confirm" onConfirm={async () => { const s = confirm.s; setConfirm(null); await run(() => svc.setStatus(r.id, s), `Mentoring ${s.toLowerCase()}`); }} />
            <Dialog open={report} onClose={() => setReport(false)} title="Report unsuitable advice"><p className="text-sm text-gray-600 mb-3">Tell the programme team what happened. Reports are reviewed by administrators.</p><Textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Describe the concern" /><div className="flex justify-end gap-2 mt-4"><Button variant="ghost" onClick={() => setReport(false)}>Cancel</Button><Button variant="danger" disabled={reason.trim().length < 10} onClick={async () => { if (await act(() => svc.report(r.id, reason), 'Report submitted')) { setReport(false); setReason(''); } }}>Submit report</Button></div></Dialog>
          </div>);
      }}</Load>
    </>
  );
}
