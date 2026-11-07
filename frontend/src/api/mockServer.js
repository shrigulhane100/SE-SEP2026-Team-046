// Dummy FastAPI-style backend (/api/v1). Same paths, status codes, RBAC and business rules
// the real backend should implement, so swapping to the real API only needs VITE_USE_MOCK=false.
import { getDb, save, nextId, resetDb } from './db';
import { ApiError } from './errors';

const H = 36e5;
const db = () => getDb();
const err = (s, d) => { throw new ApiError(s, d); };
const nowISO = () => new Date().toISOString();
const U = (id) => db().users.find((u) => u.id === id);
const SP = (uid) => db().student_profiles.find((p) => p.user_id === uid);
const MP = (uid) => db().mentor_profiles.find((p) => p.user_id === uid);
const areaName = (id) => db().guidance_areas.find((a) => a.id === id)?.name;
const sAreas = (uid) => db().student_guidance_areas.filter((x) => x.profile_id === uid).map((x) => x.area_id);
const mAreas = (uid) => db().mentor_guidance_areas.filter((x) => x.profile_id === uid).map((x) => x.area_id);
const reqOf = (rel) => db().requests.find((r) => r.id === rel.request_id);
const occupied = (mid) => db().relationships.filter((r) => ['ACTIVE', 'PAUSED'].includes(r.status) && reqOf(r).mentor_id === mid).length;
const notify = (uid, type, message, ref = null) => { const d = db(); d.notifications.push({ id: nextId(d.notifications), user_id: uid, type, message, reference_id: ref, is_read: false, created_at: nowISO() }); };
const need = (b, fields) => fields.forEach((f) => { if (b[f] === undefined || b[f] === null || b[f] === '') err(422, `${f} is required`); });

/* ---------- scheduler: runs before every call (real backend: APScheduler job) ---------- */
function expireOverdue() {
  db().requests.forEach((r) => {
    if (r.status === 'PENDING' && new Date(r.expires_at) < Date.now()) {
      r.status = 'EXPIRED';
      notify(r.student_id, 'REQUEST_EXPIRED', `Your request to ${U(r.mentor_id).name} expired without a response. Try another mentor.`, r.id);
      notify(r.mentor_id, 'REQUEST_EXPIRED', `A request from ${U(r.student_id).name} expired.`, r.id);
    }
  });
}

/* ---------- serializers ---------- */
const completion = (u) => {
  if (u.role === 'STUDENT') { const p = SP(u.id); const f = [p.roll_number, p.academic_level, p.education, p.career_stage, p.skills.length, p.interests, p.goals_summary, p.preferred_mode, p.career_objective, sAreas(u.id).length]; return Math.round(100 * f.filter(Boolean).length / f.length); }
  if (u.role === 'MENTOR') { const p = MP(u.id); const f = [p.mentor_type, p.industry, p.current_role, p.organisation, p.experience_years, p.bio, p.skills.length, p.education, mAreas(u.id).length]; return Math.round(100 * f.filter(Boolean).length / f.length); }
  return 100;
};
const userView = (u) => ({ id: u.id, name: u.name, email: u.email, role: u.role, is_active: u.is_active, created_at: u.created_at, settings: u.settings, staff_type: u.staff_type, verification_status: u.role === 'MENTOR' ? MP(u.id).verification_status : undefined, profile_completion: completion(u) });
const mentorView = (u, viewer) => {
  const p = MP(u.id); const ids = mAreas(u.id); const occ = occupied(u.id);
  let match = null;
  if (viewer?.role === 'STUDENT') { const want = sAreas(viewer.id); if (want.length) match = Math.round(100 * ids.filter((i) => want.includes(i)).length / want.length); }
  return { id: u.id, name: u.name, mentor_type: p.mentor_type, industry: p.industry, current_role: p.current_role, organisation: p.organisation, experience_years: p.experience_years, bio: p.bio, skills: p.skills, past_roles: p.past_roles, education: p.education, area_ids: ids, areas: ids.map(areaName), max_mentees: p.max_mentees, active_mentees: occ, is_accepting: p.is_accepting, verification_status: p.verification_status, available: p.is_accepting && p.verification_status === 'VERIFIED' && u.is_active && occ < p.max_mentees, match };
};
const studentBrief = (id) => { const u = U(id); const p = SP(id); return { id, name: u.name, roll_number: p?.roll_number, education: p?.education, career_stage: p?.career_stage, career_objective: p?.career_objective }; };
const reqView = (r, hideText = false) => {
  const rel = db().relationships.find((x) => x.request_id === r.id); const m = U(r.mentor_id); const base = { ...r, area: areaName(r.area_id), student: studentBrief(r.student_id), mentor: { id: m.id, name: m.name, current_role: MP(m.id).current_role }, relationship_id: rel?.id ?? null, hours_left: r.status === 'PENDING' ? Math.max(0, Math.round((new Date(r.expires_at) - Date.now()) / H)) : null };
  if (hideText) { delete base.message; delete base.objective; delete base.reject_reason; }
  return base;
};
const relView = (rel) => {
  const r = reqOf(rel); const goals = db().goals.filter((g) => g.relationship_id === rel.id); const m = U(r.mentor_id);
  return { ...rel, area: areaName(r.area_id), student: studentBrief(r.student_id), mentor: { id: m.id, name: m.name, current_role: MP(m.id).current_role, organisation: MP(m.id).organisation },
    goals: goals.map((g) => ({ ...g, created_by_name: U(g.created_by).name })),
    activities: db().activities.filter((a) => a.relationship_id === rel.id).sort((a, b) => b.created_at.localeCompare(a.created_at)).map((a) => ({ ...a, created_by_name: U(a.created_by).name })),
    feedback: db().feedback.filter((f) => f.relationship_id === rel.id).map((f) => ({ ...f, given_by_name: U(f.given_by).name })),
    progress: goals.length ? Math.round(100 * goals.filter((g) => g.status === 'DONE').length / goals.length) : 0 };
};
const ownRel = (id, user) => { const rel = db().relationships.find((r) => r.id === +id); if (!rel) err(404, 'Relationship not found'); const r = reqOf(rel); if (r.student_id !== user.id && r.mentor_id !== user.id) err(403, 'Not a participant of this relationship'); return { rel, r }; };
const other = (r, user) => (user.id === r.student_id ? r.mentor_id : r.student_id);

/* ---------- router ---------- */
const routes = [];
const route = (method, path, roles, fn) => routes.push({ method, roles, fn, re: new RegExp('^' + path.replace(/:(\w+)/g, '(?<$1>[^/]+)') + '$') });
const ANY = '*', S = ['STUDENT'], M = ['MENTOR'], A = ['ADMIN'], SM = ['STUDENT', 'MENTOR'];

export function handle({ method, path, params = {}, data = {}, token }) {
  expireOverdue();
  const r = routes.find((x) => x.method === method && x.re.test(path));
  if (!r) err(404, `No route ${method} ${path}`);
  let user = null;
  if (r.roles) {
    const id = token && token.startsWith('mock-jwt.') ? +token.split('.')[1] : null;
    user = id && U(id);
    if (!user) err(401, 'Not authenticated');
    if (!user.is_active) err(403, 'Your account has been deactivated');
    if (r.roles !== ANY && !r.roles.includes(user.role)) err(403, 'You do not have permission for this action');
  }
  const res = r.fn({ user, p: path.match(r.re).groups || {}, q: params, b: data });
  save();
  return res === undefined ? null : res;
}

/* ---------- auth ---------- */
route('POST', '/auth/login', null, ({ b }) => {
  need(b, ['email', 'password']);
  const u = db().users.find((x) => x.email.toLowerCase() === b.email.toLowerCase());
  if (!u || u.password !== b.password) err(401, 'Incorrect email or password');
  if (!u.is_active) err(403, 'Your account has been deactivated');
  return { access_token: `mock-jwt.${u.id}`, token_type: 'bearer', user: userView(u) };
});
route('POST', '/auth/register', null, ({ b }) => {
  need(b, ['name', 'email', 'password', 'role']); const d = db();
  if (!['STUDENT', 'MENTOR'].includes(b.role)) err(403, 'Only student and mentor accounts can self-register');
  if (b.password.length < 6) err(422, 'Password must be at least 6 characters');
  if (d.users.some((x) => x.email.toLowerCase() === b.email.toLowerCase())) err(409, 'An account with this email already exists');
  if (b.role === 'STUDENT') { need(b, ['roll_number']); if (d.student_profiles.some((p) => p.roll_number === b.roll_number)) err(409, 'This roll number is already registered'); }
  const id = nextId(d.users);
  d.users.push({ id, role: b.role, name: b.name, email: b.email, password: b.password, is_active: true, created_at: nowISO(), settings: { email_notifications: false } });
  if (b.role === 'STUDENT') d.student_profiles.push({ id, user_id: id, roll_number: b.roll_number, academic_level: '', education: '', career_stage: '', skills: [], interests: '', goals_summary: '', preferred_mode: '', career_objective: b.career_objective || '' });
  else { d.mentor_profiles.push({ id, user_id: id, mentor_type: b.mentor_type || '', industry: '', current_role: '', organisation: '', experience_years: 0, bio: '', skills: [], past_roles: [], education: '', max_mentees: 3, is_accepting: true, verification_status: 'PENDING' }); d.users.filter((u) => u.role === 'ADMIN').forEach((a) => notify(a.id, 'MENTOR_REGISTERED', `${b.name} registered as a mentor and awaits verification.`, id)); }
  return { access_token: `mock-jwt.${id}`, token_type: 'bearer', user: userView(U(id)) };
});
route('GET', '/auth/me', ANY, ({ user }) => userView(user));
route('PATCH', '/auth/me', ANY, ({ user, b }) => { if (b.name) user.name = b.name; if (b.settings) user.settings = { ...user.settings, ...b.settings }; return userView(user); });
route('POST', '/auth/change-password', ANY, ({ user, b }) => { if (b.current_password !== user.password) err(400, 'Current password is incorrect'); if (!b.new_password || b.new_password.length < 6) err(422, 'New password must be at least 6 characters'); user.password = b.new_password; return { ok: true }; });
route('POST', '/dev/reset', null, () => { resetDb(); return { ok: true }; });

/* ---------- reference data ---------- */
route('GET', '/guidance-areas', null, () => db().guidance_areas.filter((a) => a.is_active));
route('GET', '/meta', null, () => ({ industries: [...new Set(db().mentor_profiles.map((p) => p.industry).filter(Boolean))].sort(), mentor_types: ['Recent Graduate', 'Industry Professional', 'Research Mentor', 'Entrepreneur', 'Faculty'], activity_types: ['MEETING', 'RESUME_REVIEW', 'MOCK_INTERVIEW', 'CHECK_IN', 'OTHER'], career_objectives: ['PLACEMENT', 'HIGHER_STUDIES', 'ENTREPRENEURSHIP', 'CAREER_CLARITY'] }));

/* ---------- profile ---------- */
route('GET', '/profile/me', SM, ({ user }) => ({ user: userView(user), profile: user.role === 'STUDENT' ? SP(user.id) : MP(user.id), area_ids: user.role === 'STUDENT' ? sAreas(user.id) : mAreas(user.id) }));
route('PUT', '/profile/me', SM, ({ user, b }) => {
  const d = db(); const p = user.role === 'STUDENT' ? SP(user.id) : MP(user.id);
  if (b.name) user.name = b.name;
  if (user.role === 'STUDENT') {
    if (b.roll_number && d.student_profiles.some((x) => x.roll_number === b.roll_number && x.user_id !== user.id)) err(409, 'This roll number is already registered');
    ['roll_number', 'academic_level', 'education', 'career_stage', 'skills', 'interests', 'goals_summary', 'preferred_mode', 'career_objective'].forEach((k) => { if (b[k] !== undefined) p[k] = b[k]; });
    if (b.area_ids) { d.student_guidance_areas = d.student_guidance_areas.filter((x) => x.profile_id !== user.id); b.area_ids.forEach((a) => d.student_guidance_areas.push({ profile_id: user.id, area_id: a })); }
  } else {
    if (b.max_mentees !== undefined && +b.max_mentees < Math.max(1, occupied(user.id))) err(422, `Maximum mentees cannot be below your current ${occupied(user.id)} active mentee(s)`);
    ['mentor_type', 'industry', 'current_role', 'organisation', 'experience_years', 'bio', 'skills', 'past_roles', 'education', 'max_mentees', 'is_accepting'].forEach((k) => { if (b[k] !== undefined) p[k] = b[k]; });
    if (b.area_ids) { d.mentor_guidance_areas = d.mentor_guidance_areas.filter((x) => x.profile_id !== user.id); b.area_ids.forEach((a) => d.mentor_guidance_areas.push({ profile_id: user.id, area_id: a })); }
  }
  return { user: userView(user), profile: p, area_ids: user.role === 'STUDENT' ? sAreas(user.id) : mAreas(user.id) };
});

/* ---------- discovery ---------- */
const listMentors = (viewer, q) => {
  let list = db().users.filter((u) => u.role === 'MENTOR' && u.is_active && MP(u.id).verification_status === 'VERIFIED').map((u) => mentorView(u, viewer));
  if (q.q) { const s = q.q.toLowerCase(); list = list.filter((m) => [m.name, m.current_role, m.organisation, ...m.skills].join(' ').toLowerCase().includes(s)); }
  if (q.area_id) list = list.filter((m) => m.area_ids.includes(+q.area_id));
  if (q.industry) list = list.filter((m) => m.industry === q.industry);
  if (q.mentor_type) list = list.filter((m) => m.mentor_type === q.mentor_type);
  if (q.availability === 'available') list = list.filter((m) => m.available);
  if (q.min_experience) list = list.filter((m) => m.experience_years >= +q.min_experience);
  list.sort(q.sort === 'experience' ? (a, b) => b.experience_years - a.experience_years : (a, b) => Number(b.available) - Number(a.available) || (b.match ?? 0) - (a.match ?? 0) || b.experience_years - a.experience_years);
  return list;
};
route('GET', '/public/mentors', null, ({ q }) => listMentors(null, q).slice(0, +q.limit || 50));
route('GET', '/mentors', S, ({ user, q }) => listMentors(user, q));
route('GET', '/mentors/:id', S, ({ user, p }) => { const u = U(+p.id); if (!u || u.role !== 'MENTOR' || MP(u.id).verification_status !== 'VERIFIED') err(404, 'Mentor not found'); return mentorView(u, user); });

/* ---------- requests ---------- */
route('POST', '/requests', S, ({ user, b }) => {
  need(b, ['mentor_id', 'area_id', 'message', 'type']); const d = db();
  const m = U(+b.mentor_id); if (!m || m.role !== 'MENTOR') err(404, 'Mentor not found');
  const mv = mentorView(m);
  if (mv.verification_status !== 'VERIFIED') err(409, 'This mentor is not verified yet');
  if (!mv.is_accepting) err(409, 'This mentor is not accepting requests right now');
  if (mv.active_mentees >= mv.max_mentees) err(409, 'This mentor is at full capacity');
  if (!mv.area_ids.includes(+b.area_id)) err(422, 'This mentor does not offer the selected guidance area');
  if (b.message.trim().length < 20) err(422, 'Message must be at least 20 characters');
  if (d.requests.some((r) => r.student_id === user.id && r.mentor_id === m.id && r.status === 'PENDING')) err(409, 'You already have a pending request to this mentor');
  const r = { id: nextId(d.requests), student_id: user.id, mentor_id: m.id, area_id: +b.area_id, message: b.message.trim(), objective: (b.objective || '').trim(), type: b.type, status: 'PENDING', created_at: nowISO(), expires_at: new Date(Date.now() + 48 * H).toISOString(), responded_at: null, reject_reason: null };
  d.requests.push(r); notify(m.id, 'NEW_REQUEST', `New mentoring request from ${user.name}.`, r.id);
  return reqView(r);
});
route('GET', '/requests', SM, ({ user, q }) => db().requests.filter((r) => (user.role === 'STUDENT' ? r.student_id === user.id : r.mentor_id === user.id) && (!q.status || r.status === q.status)).sort((a, b) => b.created_at.localeCompare(a.created_at)).map((r) => reqView(r)));
const ownReq = (id, user, field) => { const r = db().requests.find((x) => x.id === +id); if (!r || r[field] !== user.id) err(404, 'Request not found'); if (r.status !== 'PENDING') err(409, `Request is already ${r.status.toLowerCase()}`); return r; };
route('POST', '/requests/:id/accept', M, ({ user, p }) => {
  const r = ownReq(p.id, user, 'mentor_id'); const d = db(); const mp = MP(user.id);
  if (occupied(user.id) >= mp.max_mentees) err(409, 'Mentoring capacity reached. Complete or close a relationship first.');
  r.status = 'ACCEPTED'; r.responded_at = nowISO();
  const rel = { id: nextId(d.relationships), request_id: r.id, status: 'ACTIVE', type: r.type, started_at: nowISO(), ended_at: null }; d.relationships.push(rel);
  notify(r.student_id, 'REQUEST_ACCEPTED', `${user.name} accepted your mentoring request.`, rel.id);
  return { request: reqView(r), relationship: relView(rel) };
});
route('POST', '/requests/:id/reject', M, ({ user, p, b }) => { const r = ownReq(p.id, user, 'mentor_id'); r.status = 'REJECTED'; r.responded_at = nowISO(); r.reject_reason = b.reason || null; notify(r.student_id, 'REQUEST_REJECTED', `${user.name} declined your request.`, r.id); return reqView(r); });
route('POST', '/requests/:id/cancel', S, ({ user, p }) => { const r = ownReq(p.id, user, 'student_id'); r.status = 'CANCELLED'; notify(r.mentor_id, 'REQUEST_CANCELLED', `${user.name} cancelled a request.`, r.id); return reqView(r); });

/* ---------- relationships, goals, activities ---------- */
route('GET', '/relationships', SM, ({ user }) => db().relationships.filter((rel) => { const r = reqOf(rel); return r.student_id === user.id || r.mentor_id === user.id; }).sort((a, b) => b.started_at.localeCompare(a.started_at)).map(relView));
route('GET', '/relationships/:id', SM, ({ user, p }) => relView(ownRel(p.id, user).rel));
const TRANSITIONS = { ACTIVE: ['PAUSED', 'COMPLETED', 'CLOSED'], PAUSED: ['ACTIVE', 'COMPLETED', 'CLOSED'], COMPLETED: [], CLOSED: [] };
route('PATCH', '/relationships/:id/status', SM, ({ user, p, b }) => {
  const { rel, r } = ownRel(p.id, user);
  if (!TRANSITIONS[rel.status].includes(b.status)) err(409, `Cannot change a ${rel.status.toLowerCase()} relationship to ${String(b.status).toLowerCase()}`);
  if (b.status === 'CLOSED' && user.role !== 'MENTOR') err(403, 'Only the mentor can close a relationship');
  rel.status = b.status; if (['COMPLETED', 'CLOSED'].includes(b.status)) rel.ended_at = nowISO();
  notify(other(r, user), 'RELATIONSHIP_UPDATED', `${user.name} marked your mentoring as ${b.status.toLowerCase()}.`, rel.id);
  return relView(rel);
});
route('POST', '/relationships/:id/goals', SM, ({ user, p, b }) => {
  const { rel, r } = ownRel(p.id, user); need(b, ['title']); const d = db();
  if (!['ACTIVE', 'PAUSED'].includes(rel.status)) err(409, 'Goals can only be added to open relationships');
  d.goals.push({ id: nextId(d.goals), relationship_id: rel.id, title: b.title.trim(), status: 'TODO', created_by: user.id, created_at: nowISO() });
  notify(other(r, user), 'GOAL_ADDED', `${user.name} added a goal: ${b.title.trim()}`, rel.id); return relView(rel);
});
route('PATCH', '/goals/:id', SM, ({ user, p, b }) => {
  const g = db().goals.find((x) => x.id === +p.id); if (!g) err(404, 'Goal not found'); const { rel } = ownRel(g.relationship_id, user);
  if (!['TODO', 'IN_PROGRESS', 'DONE'].includes(b.status)) err(422, 'Invalid goal status'); g.status = b.status; return relView(rel);
});
route('POST', '/relationships/:id/activities', SM, ({ user, p, b }) => {
  const { rel, r } = ownRel(p.id, user); need(b, ['activity_type', 'notes']); const d = db();
  d.activities.push({ id: nextId(d.activities), relationship_id: rel.id, activity_type: b.activity_type, notes: b.notes.trim(), activity_date: b.activity_date || nowISO().slice(0, 10), created_by: user.id, created_at: nowISO() });
  notify(other(r, user), 'ACTIVITY_LOGGED', `${user.name} logged an activity.`, rel.id); return relView(rel);
});
route('POST', '/relationships/:id/feedback', SM, ({ user, p, b }) => {
  const { rel, r } = ownRel(p.id, user); const d = db(); const rating = +b.rating;
  if (!(rating >= 1 && rating <= 5)) err(422, 'Rating must be between 1 and 5');
  let f = d.feedback.find((x) => x.relationship_id === rel.id && x.given_by === user.id);
  if (f) { f.rating = rating; f.comments = b.comments || ''; } else d.feedback.push({ id: nextId(d.feedback), relationship_id: rel.id, given_by: user.id, rating, comments: b.comments || '', created_at: nowISO() });
  notify(other(r, user), 'FEEDBACK_RECEIVED', `${user.name} shared feedback.`, rel.id); return relView(rel);
});
route('POST', '/relationships/:id/report', S, ({ user, p, b }) => { const { rel } = ownRel(p.id, user); need(b, ['reason']); const d = db(); d.reports.push({ id: nextId(d.reports), relationship_id: rel.id, reported_by: user.id, reason: b.reason.trim(), status: 'OPEN', created_at: nowISO() }); return { ok: true }; });
route('GET', '/feedback', SM, ({ user }) => {
  const rels = db().relationships.filter((rel) => { const r = reqOf(rel); return user.role === 'MENTOR' ? r.mentor_id === user.id : r.student_id === user.id; }).map((r) => r.id);
  const items = db().feedback.filter((f) => rels.includes(f.relationship_id) && (user.role === 'MENTOR' ? f.given_by !== user.id : f.given_by === user.id)).map((f) => { const rel = db().relationships.find((r) => r.id === f.relationship_id); return { ...f, given_by_name: U(f.given_by).name, area: areaName(reqOf(rel).area_id) }; });
  return { items, average: items.length ? +(items.reduce((s, f) => s + f.rating, 0) / items.length).toFixed(1) : null };
});

/* ---------- notifications ---------- */
route('GET', '/notifications', ANY, ({ user }) => { const items = db().notifications.filter((n) => n.user_id === user.id).sort((a, b) => b.created_at.localeCompare(a.created_at)); return { items, unread: items.filter((n) => !n.is_read).length }; });
route('POST', '/notifications/read-all', ANY, ({ user }) => { db().notifications.filter((n) => n.user_id === user.id).forEach((n) => { n.is_read = true; }); return { ok: true }; });
route('POST', '/notifications/:id/read', ANY, ({ user, p }) => { const n = db().notifications.find((x) => x.id === +p.id && x.user_id === user.id); if (n) n.is_read = true; return { ok: true }; });

/* ---------- role dashboards ---------- */
route('GET', '/dashboard', SM, ({ user }) => {
  const d = db(); const rels = d.relationships.filter((rel) => { const r = reqOf(rel); return user.role === 'STUDENT' ? r.student_id === user.id : r.mentor_id === user.id; }).map(relView);
  const open = rels.filter((r) => ['ACTIVE', 'PAUSED'].includes(r.status)); const goals = rels.flatMap((r) => r.goals);
  const notes = d.notifications.filter((n) => n.user_id === user.id).sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5);
  if (user.role === 'STUDENT') {
    const mine = d.requests.filter((r) => r.student_id === user.id);
    return { stats: { active_mentors: open.length, pending_requests: mine.filter((r) => r.status === 'PENDING').length, goals_completed: goals.filter((g) => g.status === 'DONE').length, goals_total: goals.length }, profile_completion: completion(user), relationships: open, recommended: listMentors(user, { availability: 'available' }).slice(0, 3), recent_activity: notes, suggested_area: areaName(sAreas(user.id)[0]) || 'Career Clarity', requests_total: mine.length };
  }
  const mp = MP(user.id); const pend = d.requests.filter((r) => r.mentor_id === user.id && r.status === 'PENDING');
  const fb = d.feedback.filter((f) => rels.some((r) => r.id === f.relationship_id) && f.given_by !== user.id);
  return { stats: { active_mentees: open.length, pending_requests: pend.length, max_mentees: mp.max_mentees, is_accepting: mp.is_accepting, verification_status: mp.verification_status, average_rating: fb.length ? +(fb.reduce((s, f) => s + f.rating, 0) / fb.length).toFixed(1) : null }, inbox_preview: pend.slice(0, 3).map((r) => reqView(r)), recent_activities: rels.flatMap((r) => r.activities.map((a) => ({ ...a, student: r.student.name }))).sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5), priorities: rels.filter((r) => r.status === 'ACTIVE').flatMap((r) => r.goals.filter((g) => g.status !== 'DONE').map((g) => ({ ...g, student: r.student.name, relationship_id: r.id }))).slice(0, 5), recent_activity: notes, profile_completion: completion(user) };
});

/* ---------- admin (aggregate only: never returns private notes or goal text) ---------- */
const cutoff = (q) => (q.days ? Date.now() - +q.days * 24 * H : 0);
route('GET', '/admin/stats', A, ({ q }) => {
  const d = db(); const reqs = d.requests.filter((r) => new Date(r.created_at) >= cutoff(q)); const c = (s) => reqs.filter((r) => r.status === s).length; const decided = c('ACCEPTED') + c('REJECTED') + c('EXPIRED');
  const demand = d.guidance_areas.map((a) => ({ name: a.name, value: reqs.filter((r) => r.area_id === a.id).length })).sort((a, b) => b.value - a.value);
  const now = new Date(); const registrations = [5, 4, 3, 2, 1, 0].map((i) => { const m = new Date(now.getFullYear(), now.getMonth() - i, 1); const inM = (u) => { const t = new Date(u.created_at); return t.getFullYear() === m.getFullYear() && t.getMonth() === m.getMonth(); }; return { month: m.toLocaleString('en', { month: 'short' }), students: d.users.filter((u) => u.role === 'STUDENT' && inM(u)).length, mentors: d.users.filter((u) => u.role === 'MENTOR' && inM(u)).length }; });
  const responded = reqs.filter((r) => r.responded_at && ['ACCEPTED', 'REJECTED'].includes(r.status));
  return {
    totals: { students: d.users.filter((u) => u.role === 'STUDENT').length, mentors: d.users.filter((u) => u.role === 'MENTOR').length, active_relationships: d.relationships.filter((r) => r.status === 'ACTIVE').length, pending_requests: d.requests.filter((r) => r.status === 'PENDING').length, pending_verifications: d.mentor_profiles.filter((p) => p.verification_status === 'PENDING').length, open_reports: d.reports.filter((r) => r.status === 'OPEN').length, total_requests: reqs.length },
    acceptance_rate: decided ? Math.round(100 * c('ACCEPTED') / decided) : 0,
    avg_response_hours: responded.length ? +(responded.reduce((s, r) => s + (new Date(r.responded_at) - new Date(r.created_at)) / H, 0) / responded.length).toFixed(1) : null,
    request_status: ['PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CANCELLED'].map((s) => ({ name: s, value: c(s) })), demand, registrations,
    mentor_types: ['Recent Graduate', 'Industry Professional', 'Research Mentor', 'Entrepreneur', 'Faculty'].map((t) => ({ name: t, value: d.mentor_profiles.filter((p) => p.mentor_type === t).length })),
    participation: { students_with_request: new Set(d.requests.map((r) => r.student_id)).size, mentors_with_mentee: new Set(d.relationships.filter((r) => ['ACTIVE', 'PAUSED'].includes(r.status)).map((r) => reqOf(r).mentor_id)).size },
  };
});
route('GET', '/admin/activity', A, () => {
  const d = db();
  const ev = [...d.requests.map((r) => ({ at: r.created_at, text: `${U(r.student_id).name} requested ${U(r.mentor_id).name}`, kind: 'REQUEST', status: r.status })), ...d.relationships.map((r) => ({ at: r.started_at, text: `Mentoring started: ${U(reqOf(r).student_id).name} with ${U(reqOf(r).mentor_id).name}`, kind: 'RELATIONSHIP', status: r.status })), ...d.users.filter((u) => u.role !== 'ADMIN').map((u) => ({ at: u.created_at, text: `${u.name} joined as ${u.role.toLowerCase()}`, kind: 'USER', status: u.role }))];
  return ev.sort((a, b) => b.at.localeCompare(a.at)).slice(0, 8);
});
route('GET', '/admin/users', A, ({ q }) => db().users.filter((u) => (!q.role || u.role === q.role) && (!q.q || (u.name + u.email).toLowerCase().includes(q.q.toLowerCase()))).map(userView));
route('PATCH', '/admin/users/:id', A, ({ user, p, b }) => { const u = U(+p.id); if (!u) err(404, 'User not found'); if (u.id === user.id) err(409, 'You cannot deactivate your own account'); u.is_active = !!b.is_active; return userView(u); });
route('GET', '/admin/mentor-verifications', A, () => db().users.filter((u) => u.role === 'MENTOR').map((u) => ({ ...mentorView(u), email: u.email, registered_at: u.created_at })).sort((a, b) => (a.verification_status === 'PENDING' ? -1 : 1) - (b.verification_status === 'PENDING' ? -1 : 1)));
route('POST', '/admin/mentors/:id/verify', A, ({ p, b }) => { const mp = MP(+p.id); if (!mp) err(404, 'Mentor not found'); mp.verification_status = b.approve ? 'VERIFIED' : 'REJECTED'; notify(+p.id, 'VERIFICATION', b.approve ? 'Your mentor profile is verified. Students can now find you.' : 'Your mentor profile was not verified. Please update your details.', null); return { ok: true }; });
route('GET', '/admin/requests', A, ({ q }) => db().requests.filter((r) => (!q.status || r.status === q.status) && (!q.q || (U(r.student_id).name + U(r.mentor_id).name).toLowerCase().includes(q.q.toLowerCase()))).sort((a, b) => b.created_at.localeCompare(a.created_at)).map((r) => reqView(r, true)));
route('GET', '/admin/relationships', A, ({ q }) => db().relationships.filter((r) => !q.status || r.status === q.status).map((rel) => { const r = reqOf(rel); const v = relView(rel); return { id: rel.id, status: rel.status, type: rel.type, started_at: rel.started_at, area: v.area, student: { id: r.student_id, name: v.student.name }, mentor: { id: r.mentor_id, name: v.mentor.name }, goals_total: v.goals.length, progress: v.progress, activities_count: v.activities.length }; }));
route('GET', '/admin/reports', A, () => db().reports.map((r) => { const rel = db().relationships.find((x) => x.id === r.relationship_id); const q = reqOf(rel); return { ...r, student: U(r.reported_by).name, mentor: U(q.mentor_id).name }; }).sort((a, b) => b.created_at.localeCompare(a.created_at)));
route('POST', '/admin/reports/:id/review', A, ({ p }) => { const r = db().reports.find((x) => x.id === +p.id); if (!r) err(404, 'Report not found'); r.status = 'REVIEWED'; return { ok: true }; });
route('GET', '/admin/guidance-areas', A, () => db().guidance_areas.map((a) => ({ ...a, requests: db().requests.filter((r) => r.area_id === a.id).length, mentors: db().mentor_guidance_areas.filter((x) => x.area_id === a.id).length })));
route('POST', '/admin/guidance-areas', A, ({ b }) => { need(b, ['name']); const d = db(); if (d.guidance_areas.some((a) => a.name.toLowerCase() === b.name.trim().toLowerCase())) err(409, 'Guidance area already exists'); const a = { id: nextId(d.guidance_areas), name: b.name.trim(), is_active: true }; d.guidance_areas.push(a); return a; });
route('PATCH', '/admin/guidance-areas/:id', A, ({ p, b }) => { const a = db().guidance_areas.find((x) => x.id === +p.id); if (!a) err(404, 'Not found'); if (b.name) a.name = b.name; if (b.is_active !== undefined) a.is_active = !!b.is_active; return a; });
