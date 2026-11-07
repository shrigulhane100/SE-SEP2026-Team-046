import { useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Info } from 'lucide-react';
import { Button, Card, Dialog, Field, Progress, Select, Tag, Textarea } from '../../components/ui';
import { AvailabilityBadge, ProfileHeader } from '../../components/common/Cards';
import { Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { mentorService } from '../../services/mentorService';
import { requestService } from '../../services/requestService';
import { act } from '../../lib/utils';

const schema = z.object({ area_id: z.string().min(1, 'Choose a guidance area'), message: z.string().trim().min(20, 'Please write at least 20 characters'), objective: z.string().trim().min(5, 'Describe your objective briefly'), type: z.enum(['ONE_TIME', 'LONG_TERM']) });
function RequestDialog({ m, open, onClose, onDone }) {
  const f = useForm({ resolver: zodResolver(schema), defaultValues: { area_id: m.area_ids.length === 1 ? String(m.area_ids[0]) : '', message: '', objective: '', type: 'LONG_TERM' } });
  const e = f.formState.errors;
  const submit = async (v) => { const r = await act(() => requestService.create({ ...v, mentor_id: m.id, area_id: +v.area_id }), 'Request sent. It will stay pending for up to 48 hours.'); if (r) { onDone(); onClose(); } };
  return (
    <Dialog open={open} onClose={onClose} title={`Request mentoring from ${m.name}`} wide>
      <form onSubmit={f.handleSubmit(submit)} className="grid gap-4" noValidate>
        <Field label="Guidance area" error={e.area_id?.message}><Select {...f.register('area_id')}><option value="">Select…</option>{m.area_ids.map((id, i) => <option key={id} value={id}>{m.areas[i]}</option>)}</Select></Field>
        <Field label="What guidance do you need?" error={e.message?.message} hint="Prompt: what you've tried, where you're stuck, what would help most."><Textarea {...f.register('message')} /></Field>
        <Field label="Your objective" error={e.objective?.message}><Textarea className="!h-20" placeholder="e.g. Clear technical interviews by March" {...f.register('objective')} /></Field>
        <Field label="Mentoring type"><Select {...f.register('type')}><option value="ONE_TIME">One-time conversation</option><option value="LONG_TERM">Long-term mentoring</option></Select></Field>
        <p className="text-xs text-gray-500 flex gap-2"><Info size={14} className="shrink-0 mt-0.5" />Mentoring offers guidance and feedback. It does not include referrals or placement guarantees. Unanswered requests expire after 48 hours.</p>
        <div className="flex justify-end gap-2"><Button variant="ghost" onClick={onClose}>Cancel</Button><Button type="submit" variant="accent" loading={f.formState.isSubmitting}>Send request</Button></div>
      </form>
    </Dialog>
  );
}
export default function MentorDetail() {
  const { id } = useParams(); const [sp, setSp] = useSearchParams(); const [open, setOpen] = useState(sp.get('request') === '1');
  const q = useAsync(async () => ({ m: await mentorService.get(id), reqs: await requestService.list('PENDING') }), [id]);
  return (
    <>
      <Link to="/student/mentors" className="inline-flex items-center gap-1 text-sm text-brand font-semibold mb-4"><ArrowLeft size={14} />Back to mentors</Link>
      <Load q={q} rows={2} className="h-64">{({ m, reqs }) => {
        const pending = reqs.find((r) => r.mentor.id === m.id);
        return (
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 grid gap-4">
              <Card><div className="flex flex-wrap justify-between gap-3"><ProfileHeader name={m.name} sub={`${m.current_role} · ${m.organisation}`} size={72}><div className="mt-2"><AvailabilityBadge m={m} /></div></ProfileHeader>{m.match !== null && <div className="text-right"><div className="text-3xl font-head font-extrabold text-accent">{m.match}%</div><div className="text-xs text-gray-500">match with your goals</div></div>}</div><p className="mt-4 text-gray-700">{m.bio}</p></Card>
              <Card><h2 className="font-bold mb-3">Experience</h2><dl className="grid sm:grid-cols-2 gap-3 text-sm"><div><dt className="text-gray-500">Industry</dt><dd className="font-medium">{m.industry}</dd></div><div><dt className="text-gray-500">Mentor type</dt><dd className="font-medium">{m.mentor_type}</dd></div><div><dt className="text-gray-500">Experience</dt><dd className="font-medium">{m.experience_years} years</dd></div><div><dt className="text-gray-500">Education</dt><dd className="font-medium">{m.education || '—'}</dd></div></dl>{m.past_roles.length > 0 && <><h3 className="text-sm text-gray-500 mt-4 mb-1">Previous roles</h3><ul className="text-sm list-disc pl-5">{m.past_roles.map((r) => <li key={r}>{r}</li>)}</ul></>}</Card>
              <Card><h2 className="font-bold mb-3">Expertise and guidance areas</h2><div className="flex flex-wrap gap-2">{m.skills.map((s) => <Tag key={s}>{s}</Tag>)}{m.areas.map((s) => <Tag key={s} className="bg-peach/25 text-orange-900">{s}</Tag>)}</div></Card>
            </div>
            <div className="grid gap-4 content-start">
              <Card><h2 className="font-bold mb-2">Mentoring capacity</h2><div className="text-3xl font-head font-extrabold">{m.active_mentees} / {m.max_mentees}</div><Progress value={(100 * m.active_mentees) / m.max_mentees} className="my-2" /><p className="text-xs text-gray-500">Active mentees out of maximum capacity.</p>
                {pending ? <div className="mt-4 text-sm bg-amber-50 rounded-xl p-3">You have a pending request to this mentor.<Link to="/student/requests" className="block font-semibold text-brand mt-1">View my requests</Link></div> : <Button variant="accent" className="w-full mt-4" disabled={!m.available} onClick={() => setOpen(true)}>Send Mentoring Request</Button>}
                {!m.available && !pending && <p className="text-xs text-gray-500 mt-2">This mentor can't take new requests right now.</p>}</Card>
              <Card className="bg-pale/50"><h3 className="font-bold text-sm mb-1">What mentoring includes</h3><p className="text-xs text-gray-600">Career guidance, feedback on resumes and plans, and perspective from experience. It does <b>not</b> include job referrals or placement guarantees.</p></Card>
            </div>
            <RequestDialog m={m} open={open} onClose={() => { setOpen(false); sp.delete('request'); setSp(sp, { replace: true }); }} onDone={q.reload} />
          </div>);
      }}</Load>
    </>
  );
}
