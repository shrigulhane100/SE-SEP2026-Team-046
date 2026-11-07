import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './routes/ProtectedRoute';
import PublicLayout from './components/layout/PublicLayout';
import DashboardLayout from './components/layout/DashboardLayout';
import Landing from './pages/public/Landing';
import Explore from './pages/public/Explore';
import { About, HowItWorks } from './pages/public/Info';
import { Login, Register } from './pages/auth/Auth';
import StudentDashboard from './pages/student/Dashboard';
import Discover from './pages/student/Discover';
import MentorDetail from './pages/student/MentorDetail';
import MyRequests from './pages/student/Requests';
import { MentoringList } from './pages/student/Mentoring';
import StudentProfile from './pages/student/Profile';
import MentorDashboard from './pages/mentor/Dashboard';
import RequestInbox from './pages/mentor/Inbox';
import MentorProfile from './pages/mentor/Profile';
import MentorFeedback from './pages/mentor/Feedback';
import AdminDashboard from './pages/admin/Dashboard';
import Users from './pages/admin/Users';
import Verification from './pages/admin/Verification';
import { AdminRelationships, AdminRequests } from './pages/admin/Monitoring';
import Guidance from './pages/admin/Guidance';
import Analytics from './pages/admin/Analytics';
import RelationshipPage from './pages/shared/Relationship';
import GoalsOverview from './pages/shared/GoalsOverview';
import Notifications from './pages/shared/Notifications';
import Settings from './pages/shared/Settings';

const portal = (role, children) => (
  <Route path={`/${role.toLowerCase()}`} element={<ProtectedRoute role={role}><DashboardLayout role={role} /></ProtectedRoute>}>
    <Route index element={<Navigate to="dashboard" replace />} />{children}
  </Route>
);
export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}><Route path="/" element={<Landing />} /><Route path="/explore" element={<Explore />} /><Route path="/how-it-works" element={<HowItWorks />} /><Route path="/about" element={<About />} /></Route>
      <Route path="/login" element={<Login />} /><Route path="/register" element={<Register />} />
      {portal('STUDENT', <>
        <Route path="dashboard" element={<StudentDashboard />} /><Route path="mentors" element={<Discover />} /><Route path="mentors/:id" element={<MentorDetail />} />
        <Route path="requests" element={<MyRequests />} /><Route path="mentoring" element={<MentoringList role="STUDENT" />} /><Route path="mentoring/:id" element={<RelationshipPage />} />
        <Route path="goals" element={<GoalsOverview role="STUDENT" />} /><Route path="notifications" element={<Notifications />} /><Route path="profile" element={<StudentProfile />} /><Route path="settings" element={<Settings />} /></>)}
      {portal('MENTOR', <>
        <Route path="dashboard" element={<MentorDashboard />} /><Route path="profile" element={<MentorProfile />} /><Route path="requests" element={<RequestInbox />} />
        <Route path="mentees" element={<MentoringList role="MENTOR" />} /><Route path="mentees/:id" element={<RelationshipPage />} /><Route path="activities" element={<GoalsOverview role="MENTOR" />} />
        <Route path="feedback" element={<MentorFeedback />} /><Route path="notifications" element={<Notifications />} /><Route path="settings" element={<Settings />} /></>)}
      {portal('ADMIN', <>
        <Route path="dashboard" element={<AdminDashboard />} /><Route path="users" element={<Users />} /><Route path="verification" element={<Verification />} /><Route path="requests" element={<AdminRequests />} />
        <Route path="relationships" element={<AdminRelationships />} /><Route path="guidance" element={<Guidance />} /><Route path="analytics" element={<Analytics />} /><Route path="notifications" element={<Notifications />} /><Route path="settings" element={<Settings />} /></>)}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
