import { Home, Search, Send, Target, User, Inbox, Users, BarChart3, Bell, Settings, ShieldCheck, ListChecks, Link2, Tags, Star, Activity, Flag } from 'lucide-react';
export const HOME = { STUDENT: '/student/dashboard', MENTOR: '/mentor/dashboard', ADMIN: '/admin/dashboard' };
export const ACCENT = { STUDENT: '130 116 216', MENTOR: '57 127 120', ADMIN: '67 90 121' };
export const NAV = {
  STUDENT: [['dashboard', 'Overview', Home], ['mentors', 'Discover Mentors', Search], ['requests', 'My Requests', Send], ['mentoring', 'My Mentoring', Target], ['goals', 'Goals & Progress', ListChecks], ['notifications', 'Notifications', Bell], ['profile', 'My Profile', User], ['settings', 'Settings', Settings]],
  MENTOR: [['dashboard', 'Overview', Home], ['profile', 'My Profile', User], ['requests', 'Request Inbox', Inbox], ['mentees', 'My Mentees', Users], ['activities', 'Goals & Activities', ListChecks], ['feedback', 'Feedback', Star], ['notifications', 'Notifications', Bell], ['settings', 'Settings', Settings]],
  ADMIN: [['dashboard', 'Overview', BarChart3], ['users', 'User Management', Users], ['verification', 'Mentor Verification', ShieldCheck], ['requests', 'Mentoring Requests', Send], ['relationships', 'Active Relationships', Link2], ['guidance', 'Guidance Areas', Tags], ['analytics', 'Reports & Analytics', Activity], ['settings', 'Settings', Settings]],
};
export { Flag };
