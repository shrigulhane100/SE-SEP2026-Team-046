// Dummy database for the prototype. Mirrors the 12-table ER design (+ reports).
// Persisted in localStorage so the demo survives a refresh. Use Settings > Reset demo data to restart.
const KEY = 'rockstarz.db.v2';
const H = 36e5, D = 24 * H;
const ago = (ms) => new Date(Date.now() - ms).toISOString();
const ahead = (ms) => new Date(Date.now() + ms).toISOString();
export const nextId = (arr) => arr.reduce((m, x) => Math.max(m, x.id), 0) + 1;

function seed() {
  const d = { users: [], student_profiles: [], mentor_profiles: [], guidance_areas: [], student_guidance_areas: [], mentor_guidance_areas: [], requests: [], relationships: [], goals: [], activities: [], feedback: [], reports: [], notifications: [] };
  ['Placements', 'Higher Studies', 'Research', 'Entrepreneurship', 'Career Clarity', 'Presenting an Online Degree'].forEach((name, i) => d.guidance_areas.push({ id: i + 1, name, is_active: true }));
  const user = (id, role, name, email, daysAgo, x = {}) => d.users.push({ id, role, name, email, password: 'demo123', is_active: true, created_at: ago(daysAgo * D), settings: { email_notifications: false }, ...x });
  const student = (id, name, email, daysAgo, roll, objective, areas, x = {}) => {
    user(id, 'STUDENT', name, email, daysAgo);
    const p = { id, user_id: id, roll_number: roll, academic_level: 'Diploma', education: 'BS in Data Science and Applications (IITM BS)', career_stage: 'Diploma level', skills: ['Python', 'SQL'], interests: 'Software engineering, startups', goals_summary: 'Get practical career guidance.', preferred_mode: 'Online', career_objective: objective, ...x };
    d.student_profiles.push(p); areas.forEach((a) => d.student_guidance_areas.push({ profile_id: id, area_id: a }));
  };
  const mentor = (id, name, email, daysAgo, p, areas) => {
    user(id, 'MENTOR', name, email, daysAgo);
    d.mentor_profiles.push({ id, user_id: id, verification_status: 'VERIFIED', is_accepting: true, past_roles: [], ...p });
    areas.forEach((a) => d.mentor_guidance_areas.push({ profile_id: id, area_id: a }));
  };
  user(1, 'ADMIN', 'Admin Team', 'admin@rockstarz.dev', 170, { staff_type: 'PROGRAMME_ADMIN' });
  student(2, 'Alex Student', 'student@rockstarz.dev', 120, '24F2000101', 'PLACEMENT', [1, 4], { goals_summary: 'Crack technical interviews and explore building a venture.' });
  student(3, 'Riya Das', 'riya@rockstarz.dev', 100, '24F2000102', 'CAREER_CLARITY', [5, 2], { goals_summary: 'Decide between a job and higher studies.' });
  student(4, 'Neha Patel', 'neha@rockstarz.dev', 90, '24F2000103', 'PLACEMENT', [1]);
  student(5, 'Kabir Singh', 'kabir@rockstarz.dev', 80, '24F2000104', 'PLACEMENT', [1]);
  ['Sam Joseph', 'Divya Nair', 'Imran Khan', 'Lakshmi R', 'Tarun Gupta', 'Pooja Menon', 'Vivek Anand', 'Asha Thomas'].forEach((n, i) =>
    student(21 + i, n, `student${21 + i}@rockstarz.dev`, 150 - i * 19, `24F2000${110 + i}`, ['PLACEMENT', 'HIGHER_STUDIES', 'ENTREPRENEURSHIP', 'CAREER_CLARITY'][i % 4], [(i % 5) + 1]));
  mentor(11, 'Arun Kumar', 'mentor@rockstarz.dev', 140, { mentor_type: 'Industry Professional', industry: 'Information Technology', current_role: 'Senior Software Engineer', organisation: 'Sample Tech Ltd', experience_years: 6, bio: 'Helps students prepare for software interviews, internships and first-job decisions.', skills: ['React', 'Python', 'System Design'], past_roles: ['Software Engineer, Sample Startup', 'Intern, Sample Labs'], education: 'B.Tech Computer Science', max_mentees: 2 }, [1, 5, 6]);
  mentor(12, 'Priya Sharma', 'priya.m@rockstarz.dev', 135, { mentor_type: 'Research Mentor', industry: 'Research', current_role: 'Research Associate', organisation: 'Sample Research Lab', experience_years: 4, bio: 'Guides students on research pathways, publishing and MS/PhD applications.', skills: ['Deep Learning', 'Computer Vision', 'Research Writing'], education: 'M.Tech AI', max_mentees: 4 }, [3, 2]);
  mentor(13, 'Rahul Menon', 'rahul@rockstarz.dev', 130, { mentor_type: 'Entrepreneur', industry: 'Entrepreneurship', current_role: 'Founder', organisation: 'Sample Startup', experience_years: 8, bio: 'Shares practical lessons from building and funding a first venture.', skills: ['Product', 'Fundraising', 'Go-to-market'], past_roles: ['Product Manager, Sample Products'], education: 'MBA', max_mentees: 5 }, [4, 5]);
  mentor(14, 'Sneha Iyer', 'sneha@rockstarz.dev', 110, { mentor_type: 'Recent Graduate', industry: 'Analytics', current_role: 'Data Analyst', organisation: 'Sample Analytics', experience_years: 1, bio: 'Recent graduate sharing the move from online degree to a first analytics job.', skills: ['SQL', 'Tableau', 'Python'], education: 'BS Data Science (IITM BS)', max_mentees: 3, is_accepting: false }, [1, 6]);
  mentor(15, 'Dr. Vikram Rao', 'vikram@rockstarz.dev', 105, { mentor_type: 'Faculty', industry: 'Academia', current_role: 'Assistant Professor', organisation: 'Sample Institute', experience_years: 12, bio: 'Academic and research guidance for degree-level students.', skills: ['Machine Learning', 'Statistics', 'VLSI Design'], education: 'PhD', max_mentees: 4 }, [2, 3]);
  mentor(16, 'Meera Nair', 'meera@rockstarz.dev', 95, { mentor_type: 'Industry Professional', industry: 'Information Technology', current_role: 'Product Manager', organisation: 'Sample Products Inc', experience_years: 5, bio: 'Guidance on product roles, career pivots and early-career choices.', skills: ['Product Management', 'Analytics'], education: 'B.E. + PGDM', max_mentees: 3 }, [1, 4, 5]);
  mentor(17, 'Ananya Rao', 'ananya@rockstarz.dev', 2, { mentor_type: 'Recent Graduate', industry: 'Semiconductors', current_role: 'VLSI Design Engineer', organisation: 'Sample Silicon', experience_years: 2, bio: 'Alumna working in chip design; awaiting verification.', skills: ['VLSI', 'Verilog'], education: 'B.Tech ECE', max_mentees: 3, verification_status: 'PENDING' }, [1, 2]);

  const req = (id, s, m, area, status, hAgo, type, msg, x = {}) => d.requests.push({ id, student_id: s, mentor_id: m, area_id: area, message: msg, objective: 'Make steady progress toward my career goal.', type, status, created_at: ago(hAgo * H), expires_at: ago((hAgo - 48) * H), responded_at: null, reject_reason: null, ...x });
  req(1, 2, 11, 1, 'PENDING', 6, 'ONE_TIME', 'I have an interview next month and want to prepare for technical rounds.');
  req(2, 2, 13, 4, 'ACCEPTED', 216, 'LONG_TERM', 'I want to understand the practical challenges of starting a venture.', { responded_at: ago(200 * H) });
  req(3, 2, 12, 3, 'REJECTED', 288, 'LONG_TERM', 'Looking for guidance on research pathways after my diploma.', { responded_at: ago(270 * H), reject_reason: 'Currently at capacity for research students.' });
  req(4, 3, 11, 5, 'PENDING', 3, 'LONG_TERM', 'Unsure whether to pursue a job or higher studies and would like to discuss.');
  req(5, 4, 11, 1, 'ACCEPTED', 480, 'LONG_TERM', 'Need help with resume review and internship search.', { responded_at: ago(470 * H) });
  req(6, 5, 11, 1, 'EXPIRED', 170, 'ONE_TIME', 'Request from last week that was never answered.');
  req(7, 21, 11, 1, 'ACCEPTED', 1500, 'ONE_TIME', 'Quick review of my portfolio before applications.', { responded_at: ago(1490 * H) });
  req(8, 23, 12, 3, 'ACCEPTED', 400, 'LONG_TERM', 'Guidance on writing my first paper.', { responded_at: ago(390 * H) });
  req(9, 24, 15, 2, 'CANCELLED', 330, 'ONE_TIME', 'Questions about MS applications.');
  req(10, 26, 13, 4, 'ACCEPTED', 700, 'LONG_TERM', 'Want to validate a startup idea.', { responded_at: ago(690 * H) });
  req(11, 3, 16, 1, 'PENDING', 72, 'ONE_TIME', 'Would like a short chat about product roles.'); // overdue: the scheduler expires it on first load
  const rel = (id, request_id, status, hAgo, type) => d.relationships.push({ id, request_id, status, type, started_at: ago(hAgo * H), ended_at: status === 'COMPLETED' ? ago(100 * H) : null });
  rel(1, 2, 'ACTIVE', 200, 'LONG_TERM'); rel(2, 5, 'ACTIVE', 470, 'LONG_TERM'); rel(3, 7, 'COMPLETED', 1490, 'ONE_TIME'); rel(4, 8, 'ACTIVE', 390, 'LONG_TERM'); rel(5, 10, 'PAUSED', 690, 'LONG_TERM');
  const goal = (id, r, title, status, by) => d.goals.push({ id, relationship_id: r, title, status, created_by: by, created_at: ago(150 * H) });
  goal(1, 1, 'Draft a one-page venture idea', 'DONE', 13); goal(2, 1, 'Interview 3 potential users', 'IN_PROGRESS', 2); goal(3, 1, 'Build a simple prototype', 'TODO', 13);
  goal(4, 2, 'Resume review and rewrite', 'DONE', 11); goal(5, 2, 'Three mock interviews', 'IN_PROGRESS', 11); goal(6, 3, 'Portfolio review', 'DONE', 11); goal(7, 4, 'Outline paper structure', 'IN_PROGRESS', 12);
  const act = (id, r, t, notes, hAgo, by) => d.activities.push({ id, relationship_id: r, activity_type: t, notes, activity_date: ago(hAgo * H).slice(0, 10), created_by: by, created_at: ago(hAgo * H) });
  act(1, 1, 'MEETING', 'Intro call: discussed the problem space and a first idea.', 190, 13); act(2, 1, 'CHECK_IN', 'Reviewed draft idea; agreed to start user interviews.', 80, 2);
  act(3, 2, 'RESUME_REVIEW', 'Reworked the projects section.', 300, 11); act(4, 2, 'MOCK_INTERVIEW', 'First mock interview on data structures.', 120, 11); act(5, 3, 'MEETING', 'Portfolio feedback session.', 1480, 11);
  d.feedback.push({ id: 1, relationship_id: 3, given_by: 21, rating: 5, comments: 'Very practical and clear guidance.', created_at: ago(95 * H) });
  d.reports.push({ id: 1, relationship_id: 5, reported_by: 26, reason: 'The advice felt generic and the mentor stopped responding.', status: 'OPEN', created_at: ago(50 * H) });
  const note = (u, type, message, ref, hAgo, read = false) => d.notifications.push({ id: nextId(d.notifications), user_id: u, type, message, reference_id: ref, is_read: read, created_at: ago(hAgo * H) });
  note(2, 'REQUEST_ACCEPTED', 'Rahul Menon accepted your mentoring request.', 2, 200); note(2, 'REQUEST_REJECTED', 'Priya Sharma declined your request.', 3, 270, true);
  note(11, 'NEW_REQUEST', 'New mentoring request from Alex Student.', 1, 6); note(11, 'NEW_REQUEST', 'New mentoring request from Riya Das.', 4, 3);
  note(1, 'MENTOR_REGISTERED', 'Ananya Rao registered as a mentor and awaits verification.', 17, 40);
  return d;
}

let db;
export const getDb = () => {
  if (db) return db;
  try { const raw = localStorage.getItem(KEY); if (raw) { db = JSON.parse(raw); return db; } } catch { /* storage unavailable */ }
  db = seed(); save(); return db;
};
export const save = () => { try { localStorage.setItem(KEY, JSON.stringify(db)); } catch { /* ignore */ } };
export const resetDb = () => { db = seed(); save(); };
