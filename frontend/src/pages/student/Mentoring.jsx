import { Link } from 'react-router-dom';
import { Target } from 'lucide-react';
import { Button } from '../../components/ui';
import { RelationshipCard } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { relationshipService } from '../../services/relationshipService';

export const MentoringList = ({ role }) => {
  const q = useAsync(relationshipService.list, []); const base = `/${role.toLowerCase()}`;
  return (
    <>
      <PageHeader title={role === 'STUDENT' ? 'My mentoring' : 'My mentees'} sub={role === 'STUDENT' ? 'Your active, paused and completed mentoring relationships.' : 'Students you are mentoring or have mentored.'} />
      <Load q={q} rows={2} className="h-44">{(list) => list.length ? <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">{list.map((r) => <RelationshipCard key={r.id} rel={r} role={role} to={`${base}/${role === 'STUDENT' ? 'mentoring' : 'mentees'}/${r.id}`} />)}</div> : <EmptyState icon={Target} title="No relationships yet" text={role === 'STUDENT' ? 'Once a mentor accepts your request, it appears here.' : 'Accept a request to start mentoring.'} action={<Link to={role === 'STUDENT' ? '/student/mentors' : '/mentor/requests'}><Button size="sm">{role === 'STUDENT' ? 'Discover mentors' : 'Open inbox'}</Button></Link>} />}</Load>
    </>
  );
};
