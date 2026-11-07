import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button, Card, Field, Input, Progress, Select, Textarea, cn } from '../../components/ui';
import { PageHeader } from '../../components/common/PageHeader';
import { Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useAuth } from '../../hooks/useAuth';
import { profileService } from '../../services/profileService';
import { mentorService } from '../../services/mentorService';
import { act, csv, label } from '../../lib/utils';

const schema = z.object({ name: z.string().min(2, 'Enter your name'), roll_number: z.string().min(4, 'Enter your roll number'), academic_level: z.string().min(1, 'Select a level'), education: z.string().min(2, 'Enter your background'), career_stage: z.string().min(2, 'Enter your career stage'), skills: z.string(), interests: z.string().min(2, 'Add at least one interest'), goals_summary: z.string().min(10, 'Add a short goals summary'), preferred_mode: z.string().min(1, 'Choose a mode'), career_objective: z.string().min(1, 'Choose an objective'), area_ids: z.array(z.number()).min(1, 'Pick at least one guidance area') });
function Form({ data, areas, meta }) {
  const { refresh } = useAuth(); const { profile: p, user } = data;
  const f = useForm({ resolver: zodResolver(schema), defaultValues: { ...p, name: user.name, skills: p.skills.join(', '), area_ids: data.area_ids } });
  const e = f.formState.errors;
  const save = async (v) => { if (await act(() => profileService.save({ ...v, skills: csv(v.skills) }), 'Profile saved')) refresh(); };
  return (
    <form onSubmit={f.handleSubmit(save)} className="grid gap-5 max-w-3xl" noValidate>
      <Card><h2 className="font-bold mb-4">About you</h2><div className="grid sm:grid-cols-2 gap-4">
        <Field label="Full name" error={e.name?.message}><Input {...f.register('name')} /></Field>
        <Field label="Roll number" error={e.roll_number?.message}><Input {...f.register('roll_number')} /></Field>
        <Field label="Academic level" error={e.academic_level?.message}><Select {...f.register('academic_level')}><option value="">Select…</option>{['Foundation', 'Diploma', 'Degree'].map((x) => <option key={x}>{x}</option>)}</Select></Field>
        <Field label="Current career stage" error={e.career_stage?.message}><Input placeholder="e.g. Diploma level, seeking internship" {...f.register('career_stage')} /></Field>
        <Field label="Educational background" error={e.education?.message} className="sm:col-span-2"><Input {...f.register('education')} /></Field></div></Card>
      <Card><h2 className="font-bold mb-4">Goals and interests</h2><div className="grid gap-4">
        <Field label="What are you looking for?" error={e.career_objective?.message}><Select {...f.register('career_objective')}><option value="">Select…</option>{meta.career_objectives.map((o) => <option key={o} value={o}>{label(o)}</option>)}</Select></Field>
        <Field label="Skills" hint="Comma separated"><Input {...f.register('skills')} /></Field>
        <Field label="Career interests" error={e.interests?.message}><Input {...f.register('interests')} /></Field>
        <Field label="Goals summary" error={e.goals_summary?.message}><Textarea {...f.register('goals_summary')} /></Field>
        <Field label="Preferred mentoring mode" error={e.preferred_mode?.message}><Select {...f.register('preferred_mode')}><option value="">Select…</option>{['Online', 'Chat', 'Calls'].map((x) => <option key={x}>{x}</option>)}</Select></Field>
        <Controller control={f.control} name="area_ids" render={({ field }) => <Field label="Guidance areas" error={e.area_ids?.message}><div className="flex flex-wrap gap-2">{areas.map((a) => { const on = field.value.includes(a.id); return <button key={a.id} type="button" aria-pressed={on} onClick={() => field.onChange(on ? field.value.filter((x) => x !== a.id) : [...field.value, a.id])} className={cn('px-3 py-1.5 rounded-full text-sm border', on ? 'bg-accent text-white border-accent' : 'bg-white hover:bg-pale')}>{a.name}</button>; })}</div></Field>} /></div></Card>
      <div><Button type="submit" variant="accent" loading={f.formState.isSubmitting}>Save profile</Button></div>
    </form>
  );
}
export default function StudentProfile() {
  const q = useAsync(async () => ({ data: await profileService.get(), areas: await mentorService.areas(), meta: await mentorService.meta() }), []);
  return (<><PageHeader title="My profile" sub="A complete profile helps us match you with the right mentors." /><Load q={q} rows={3} className="h-48">{({ data, areas, meta }) => <><Card className="max-w-3xl mb-5"><div className="flex justify-between text-sm mb-2"><b>Profile completion</b><span>{data.user.profile_completion}%</span></div><Progress value={data.user.profile_completion} /></Card><Form data={data} areas={areas} meta={meta} /></>}</Load></>);
}
