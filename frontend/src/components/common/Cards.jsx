import { Link } from 'react-router-dom';
import { Briefcase, Clock, Sparkles, Check, X } from 'lucide-react';
import { Avatar, Button, Card, Progress, Tag, cn, label } from '../ui';
import { ago, fmtDate } from '../../lib/utils';

const TONE = { PENDING: 'bg-amber-100 text-amber-800', ACCEPTED: 'bg-emerald-100 text-emerald-800', COMPLETED: 'bg-emerald-100 text-emerald-800', DONE: 'bg-emerald-100 text-emerald-800', VERIFIED: 'bg-emerald-100 text-emerald-800', AVAILABLE: 'bg-emerald-100 text-emerald-800', REJECTED: 'bg-red-100 text-red-800', OPEN: 'bg-red-100 text-red-800', ACTIVE: 'bg-violet-100 text-violet-800', IN_PROGRESS: 'bg-violet-100 text-violet-800', PAUSED: 'bg-blue-100 text-blue-800', INFO: 'bg-blue-100 text-blue-800', EXPIRED: 'bg-gray-200 text-gray-700', CANCELLED: 'bg-gray-200 text-gray-700', CLOSED: 'bg-gray-200 text-gray-700', INACTIVE: 'bg-gray-200 text-gray-700', TODO: 'bg-gray-200 text-gray-700', UNAVAILABLE: 'bg-gray-200 text-gray-700', REVIEWED: 'bg-gray-200 text-gray-700' };
export const StatusBadge = ({ status, text }) => <span className={cn('px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap', TONE[status] || 'bg-gray-100 text-gray-700')}>{text || label(status)}</span>;
export const AvailabilityBadge = ({ m }) => <StatusBadge status={m.available ? 'AVAILABLE' : 'UNAVAILABLE'} text={m.available ? 'Available' : m.is_accepting ? 'At capacity' : 'Not accepting'} />;
export const StatCard = ({ label: l, value, icon: Icon, hint, to }) => {
  const body = (<Card className="flex items-center gap-4 h-full"><div className="w-11 h-11 rounded-xl bg-accent/10 text-accent flex items-center justify-center shrink-0">{Icon && <Icon size={20} />}</div><div className="min-w-0"><div className="text-2xl font-head font-extrabold leading-tight">{value}</div><div className="text-sm text-gray-500">{l}</div>{hint && <div className="text-xs text-gray-400 mt-0.5">{hint}</div>}</div></Card>);
  return to ? <Link to={to} className="block hover:-translate-y-0.5 transition">{body}</Link> : body;
};
export const StatsGrid = ({ children, cols = 3 }) => <div className={cn('grid grid-cols-1 sm:grid-cols-2 gap-4', cols === 3 && 'lg:grid-cols-3', cols === 4 && 'lg:grid-cols-4')}>{children}</div>;
export const ExpertiseTags = ({ items = [], max = 3 }) => <div className="flex flex-wrap gap-1.5">{items.slice(0, max).map((t) => <Tag key={t}>{t}</Tag>)}{items.length > max && <Tag className="bg-gray-100 text-gray-600">+{items.length - max}</Tag>}</div>;
export const ProfileHeader = ({ name, sub, children, size = 64 }) => (
  <div className="flex items-center gap-4"><Avatar name={name} size={size} /><div className="min-w-0"><h2 className="text-xl font-extrabold truncate">{name}</h2>{sub && <p className="text-sm text-gray-500">{sub}</p>}{children}</div></div>
);
export const MentorCard = ({ m, to = `/student/mentors/${m.id}`, requestTo = `${to}?request=1`, actions = true }) => (
  <Card className="flex flex-col gap-3 hover:shadow-md transition">
    <div className="flex items-start gap-3">
      <Avatar name={m.name} />
      <div className="min-w-0 flex-1"><div className="font-head font-bold truncate">{m.name}</div><div className="text-sm text-gray-500 truncate">{m.current_role} · {m.organisation}</div></div>
      <AvailabilityBadge m={m} />
    </div>
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500"><span className="inline-flex items-center gap-1"><Briefcase size={13} />{m.industry}</span><span className="inline-flex items-center gap-1"><Clock size={13} />{m.experience_years} yr{m.experience_years === 1 ? '' : 's'} experience</span>{m.match !== null && m.match !== undefined && <span className="inline-flex items-center gap-1 text-accent font-semibold"><Sparkles size={13} />{m.match}% match</span>}</div>
    <ExpertiseTags items={[...m.areas, ...m.skills]} />
    <p className="text-sm text-gray-600 line-clamp-2 flex-1">{m.bio}</p>
    {actions && <div className="flex gap-2 pt-1"><Link to={to} className="flex-1"><Button variant="outline" size="sm" className="w-full">View Profile</Button></Link><Link to={requestTo} className="flex-1"><Button variant="accent" size="sm" className="w-full" disabled={!m.available}>Send Request</Button></Link></div>}
  </Card>
);
export const RequestCard = ({ r, onAccept, onReject, busy }) => (
  <Card className="flex flex-col gap-3">
    <div className="flex items-start gap-3"><Avatar name={r.student.name} /><div className="flex-1 min-w-0"><div className="font-head font-bold">{r.student.name}</div><div className="text-xs text-gray-500">{r.student.education} · <span className="mono">{r.student.roll_number}</span></div></div><StatusBadge status={r.status} /></div>
    <div className="flex flex-wrap gap-2 text-xs"><Tag>{r.area}</Tag><Tag className="bg-gray-100 text-gray-700">{label(r.type)}</Tag>{r.student.career_objective && <Tag className="bg-peach/20 text-orange-800">Objective: {label(r.student.career_objective)}</Tag>}</div>
    <p className="text-sm bg-ivory rounded-xl p-3">{r.message}</p>
    {r.objective && <p className="text-xs text-gray-500"><b>Objective:</b> {r.objective}</p>}
    <div className="flex items-center justify-between gap-2 flex-wrap">
      <span className="text-xs text-gray-500">Requested {ago(r.created_at)}{r.status === 'PENDING' && <span className="text-amber-700 font-semibold"> · expires in {r.hours_left}h</span>}</span>
      {r.status === 'PENDING' && <div className="flex gap-2"><Button size="sm" variant="success" disabled={busy} onClick={() => onAccept(r)}><Check size={15} />Accept</Button><Button size="sm" variant="dangerOutline" disabled={busy} onClick={() => onReject(r)}><X size={15} />Reject</Button></div>}
      {r.status === 'REJECTED' && r.reject_reason && <span className="text-xs text-gray-500">Reason: {r.reject_reason}</span>}
    </div>
  </Card>
);
export const RelationshipCard = ({ rel, role, to }) => {
  const who = role === 'STUDENT' ? rel.mentor : rel.student; const done = rel.goals.filter((g) => g.status === 'DONE').length;
  return (
    <Card className="flex flex-col gap-3 hover:shadow-md transition">
      <div className="flex items-start gap-3"><Avatar name={who.name} /><div className="flex-1 min-w-0"><div className="font-head font-bold truncate">{who.name}</div><div className="text-xs text-gray-500">{rel.area} · {label(rel.type)} · started {fmtDate(rel.started_at)}</div></div><StatusBadge status={rel.status} /></div>
      <div><div className="flex justify-between text-xs text-gray-500 mb-1"><span>Goals {done}/{rel.goals.length}</span><span>{rel.progress}%</span></div><Progress value={rel.progress} /></div>
      <Link to={to}><Button variant="outline" size="sm" className="w-full">View relationship</Button></Link>
    </Card>
  );
};
