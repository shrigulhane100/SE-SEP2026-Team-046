import { useState } from 'react';
import { Search, SearchX } from 'lucide-react';
import { Button, Input, Select } from '../../components/ui';
import { MentorCard } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useDebounce } from '../../hooks/useDebounce';
import { mentorService } from '../../services/mentorService';

const init = { q: '', area_id: '', industry: '', mentor_type: '', availability: '', min_experience: '', sort: 'relevance' };
export default function Discover() {
  const [f, setF] = useState(init); const d = useDebounce(f.q);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const meta = useAsync(async () => ({ ...(await mentorService.meta()), areas: await mentorService.areas() }), []);
  const res = useAsync(() => mentorService.list({ ...f, q: d }), [d, f.area_id, f.industry, f.mentor_type, f.availability, f.min_experience, f.sort]);
  const m = meta.data;
  return (
    <>
      <PageHeader title="Discover mentors" sub="Find people who can guide your next step." />
      <div className="grid gap-3 mb-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="relative sm:col-span-2 lg:col-span-4"><Search size={16} className="absolute left-3 top-3.5 text-gray-400" /><Input className="pl-9" placeholder="Search by name, role or skill" value={f.q} onChange={set('q')} aria-label="Search mentors" /></div>
        <Select value={f.area_id} onChange={set('area_id')} aria-label="Guidance area"><option value="">All guidance areas</option>{m?.areas.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</Select>
        <Select value={f.industry} onChange={set('industry')} aria-label="Industry"><option value="">All industries</option>{m?.industries.map((i) => <option key={i}>{i}</option>)}</Select>
        <Select value={f.mentor_type} onChange={set('mentor_type')} aria-label="Mentor type"><option value="">All mentor types</option>{m?.mentor_types.map((i) => <option key={i}>{i}</option>)}</Select>
        <Select value={f.availability} onChange={set('availability')} aria-label="Availability"><option value="">Any availability</option><option value="available">Available now</option></Select>
        <Select value={f.min_experience} onChange={set('min_experience')} aria-label="Years of experience"><option value="">Any experience</option><option value="2">2+ years</option><option value="5">5+ years</option><option value="10">10+ years</option></Select>
        <Select value={f.sort} onChange={set('sort')} aria-label="Sort"><option value="relevance">Sort: relevance</option><option value="experience">Sort: experience</option></Select>
        <Button variant="ghost" onClick={() => setF(init)}>Clear filters</Button>
      </div>
      <Load q={res} rows={3} className="h-56">{(list) => list.length ? <><p className="text-sm text-gray-500 mb-3">{list.length} mentor{list.length > 1 ? 's' : ''}</p><div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">{list.map((x) => <MentorCard key={x.id} m={x} />)}</div></> : <EmptyState icon={SearchX} title="No mentors match" text="Try removing a filter or searching a different skill." action={<Button size="sm" onClick={() => setF(init)}>Clear filters</Button>} />}</Load>
    </>
  );
}
