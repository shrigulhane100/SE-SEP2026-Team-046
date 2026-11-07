import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { HOME } from '../config/nav';
import { LoadingState } from '../components/common/States';
// UX-level guard only. The backend must enforce RBAC on every endpoint (the mock server does too).
export default function ProtectedRoute({ role, children }) {
  const { user, loading } = useAuth(); const loc = useLocation();
  if (loading) return <div className="p-8 max-w-xl mx-auto"><LoadingState rows={3} /></div>;
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  if (user.role !== role) return <Navigate to={HOME[user.role]} replace />;
  return children;
}
