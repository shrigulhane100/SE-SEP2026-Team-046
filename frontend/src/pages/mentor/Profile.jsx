import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button, Card, Field, Input, Progress, Select, Switch, Textarea, cn } from '../../components/ui';
import { StatusBadge } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useAuth } from '../../hooks/useAuth';
import { profileService } from '../../services/profileService';
import { mentorService } from '../../services/mentorService';
import { act, csv } from '../../lib/utils';

const schema = z.object({ name: z.string().min(2), mentor_type: z.string().min(1, 'Select a type'), industry: z.string().min(2, 'Enter your industry'), current_role: z.string().min(2, 'Enter your current role'), organisation: z.string().min(2, 'Enter your organisation'), experience_years: z.coerce.number().min(0, 'Cannot be negative').max(60), bio: z.string().min(20, 'Write at least 20 characters'), skills: z.string().min(2, 'Add at least one skill'), past_roles: z.string(), education: z.string().min(2, 'Enter your education'), max_mentees: z.coerce.number().int().min(1, 'At least 1').max(20), is_accepting: z.boolean(), area_ids: z.array(z.number()).min(1, 'Pick at least one guidance area') });
function Form({ data, areas, meta }) {
  const { refresh } = useAuth(); const { profile: p, user } = data;
  const f = useForm({ resolver: zodResolver(schema), defaultValues: { ...p, name: user.name, skills: p.skills.join(', '), past_roles: p.past_roles.join(', '), area_ids: data.area_ids } }); const e = f.formState.errors;
  const save = async (v) => { if (await act(() => profileService.save({ ...v, skills: csv(v.skills), past_roles: csv(v.past_roles) }), 'Profile saved')) refresh(); };
  return (
    <form onSubmit={f.handleSubmit(save)} className="grid gap-5 max-w-3xl" noValidate>
      <Card><h2 className="font-bold mb-4">Professional details</h2><div className="grid sm:grid-cols-2 gap-4">
        <Field label="Full name" error={e.name?.message}><Input {...f.register('name')} /></Field>
        <Field label="Mentor type" error={e.mentor_type?.message}><Select {...f.register('mentor_type')}><option value="">Select…</option>{meta.mentor_types.map((t) => <option key={t}>{t}</option>)}</Select></Field>
        <Field label="Current role" error={e.current_role?.message}><Input {...f.register('current_role')} /></Field>
        <Field label="Organisation" error={e.organisation?.message}><Input {...f.register('organisation')} /></Field>
        <Field label="Industry" error={e.industry?.message}><Input {...f.register('industry')} /></Field>
        <Field label="Years of experience" error={e.experience_years?.message}><Input type="number" {...f.register('experience_years')} /></Field>
        <Field label="Educational background" error={e.education?.message} className="sm:col-span-2"><Input {...f.register('education')} /></Field>
        <Field label="Previous roles" hint="Comma separated" className="sm:col-span-2"><Input {...f.register('past_roles')} /></Field>
        <Field label="Short biography" error={e.bio?.message} className="sm:col-span-2"><Textarea {...f.register('bio')} /></Field>
        <Field label="Expertise tags" error={e.skills?.message} hint="Comma separated" className="sm:col-span-2"><Input {...f.register('skills')} /></Field></div></Card>
      <Card><h2 className="font-bold mb-4">Guidance and capacity</h2><div className="grid gap-4">
        <Controller control={f.control} name="area_ids" render={({ field }) => <Field label="Guidance areas you offer" error={e.area_ids?.message}><div className="flex flex-wrap gap-2">{areas.map((a) => { const on = field.value.includes(a.id); return <button key={a.id} type="button" aria-pressed={on} onClick={() => field.onChange(on ? field.value.filter((x) => x !== a.id) : [...field.value, a.id])} className={cn('px-3 py-1.5 rounded-full text-sm border', on ? 'bg-accent text-white border-accent' : 'bg-white hover:bg-pale')}>{a.name}</button>; })}</div></Field>} />
        <Field label="Maximum mentees" error={e.max_mentees?.message} hint="Includes active and paused relationships." className="max-w-xs"><Input type="number" {...f.register('max_mentees')} /></Field>
        <Controller control={f.control} name="is_accepting" render={({ field }) => <div className="flex items-center justify-between gap-4 p-3 rounded-xl bg-ivory"><div><div className="text-sm font-medium">Accepting new requests</div><div className="text-xs text-gray-500">Turn off to pause discovery without losing your profile.</div></div><Switch label="Accepting requests" checked={field.value} onChange={field.onChange} /></div>} /></div></Card>
      <div><Button type="submit" variant="accent" loading={f.formState.isSubmitting}>Save profile</Button></div>
    </form>
  );
}
export default function MentorProfile() {
  const q = useAsync(async () => ({ data: await profileService.get(), areas: await mentorService.areas(), meta: await mentorService.meta() }), []);
  return (<><PageHeader title="My profile" sub="This is what students see when they discover you." /><Load q={q} rows={3} className="h-48">{({ data, areas, meta }) => <><Card className="max-w-3xl mb-5"><div className="flex justify-between text-sm mb-2"><b>Profile completion</b><span className="flex items-center gap-2">{data.user.profile_completion}% <StatusBadge status={data.profile.verification_status} /></span></div><Progress value={data.user.profile_completion} /></Card><Form data={data} areas={areas} meta={meta} /></>}</Load></>);
}
