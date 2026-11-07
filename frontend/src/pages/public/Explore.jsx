import { useState } from 'react';
import { Search } from 'lucide-react';
import { Input } from '../../components/ui';
import { MentorCard } from '../../components/common/Cards';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { useDebounce } from '../../hooks/useDebounce';
import { mentorService } from '../../services/mentorService';

export default function Explore() {
  const [q, setQ] = useState(''); const d = useDebounce(q);
  const res = useAsync(() => mentorService.publicList({ q: d }), [d]);
  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-12">
      <h1 className="text-3xl font-extrabold">Explore mentors</h1><p className="text-gray-500 mt-1">Browse sample mentor profiles. Log in as a student to filter and send requests.</p>
      <div className="relative max-w-md my-6"><Search size={16} className="absolute left-3 top-3.5 text-gray-400" /><Input className="pl-9" placeholder="Search by name, role or skill" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search mentors" /></div>
      <Load q={res} rows={3} className="h-56">{(list) => list.length ? <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{list.map((m) => <MentorCard key={m.id} m={m} to="/login" requestTo="/login" />)}</div> : <EmptyState title="No mentors found" text="Try a different search." />}</Load>
    </div>
  );
}
