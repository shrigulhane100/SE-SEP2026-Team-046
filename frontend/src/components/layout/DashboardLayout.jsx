import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate, Link } from 'react-router-dom';
import { LogOut, Menu, PanelLeftClose, PanelLeftOpen, X, ChevronDown } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { NAV, ACCENT } from '../../config/nav';
import NotificationBell from '../common/NotificationBell';
import { Avatar, cn } from '../ui';
import { Logo } from './PublicLayout';

function Sidebar({ role, collapsed, onNavigate }) {
  const items = NAV[role]; const { logout } = useAuth(); const nav = useNavigate();
  return (
    <div className="flex flex-col h-full p-3">
      <Link to="/" className={cn('mb-6 mt-1 px-2', collapsed && 'mx-auto px-0')}><Logo compact={collapsed} /></Link>
      <nav className="flex-1 space-y-1" aria-label={`${role} navigation`}>
        {items.map(([to, text, Icon]) => (
          <NavLink key={to} to={`/${role.toLowerCase()}/${to}`} onClick={onNavigate} title={collapsed ? text : undefined}
            className={({ isActive }) => cn('flex items-center gap-3 h-11 px-3 rounded-xl text-sm font-medium transition', collapsed && 'justify-center px-0', isActive ? 'bg-accent text-white shadow-soft' : 'text-gray-600 hover:bg-pale')}>
            <Icon size={18} className="shrink-0" />{!collapsed && <span className="truncate">{text}</span>}
          </NavLink>))}
      </nav>
      <button onClick={() => { logout(); nav('/'); }} className={cn('flex items-center gap-3 h-11 px-3 rounded-xl text-sm text-red-600 hover:bg-red-50', collapsed && 'justify-center px-0')}><LogOut size={18} />{!collapsed && 'Logout'}</button>
    </div>
  );
}

export default function DashboardLayout({ role }) {
  const { user, logout } = useAuth(); const loc = useLocation(); const nav = useNavigate();
  const [collapsed, setCollapsed] = useState(() => { try { return localStorage.getItem('rs.sidebar') === '1'; } catch { return false; } });
  const [drawer, setDrawer] = useState(false); const [menu, setMenu] = useState(false);
  useEffect(() => { try { localStorage.setItem('rs.sidebar', collapsed ? '1' : '0'); } catch { /* ignore */ } }, [collapsed]);
  useEffect(() => { setDrawer(false); setMenu(false); }, [loc.pathname]);
  const current = NAV[role].find(([to]) => loc.pathname.startsWith(`/${role.toLowerCase()}/${to}`));
  const mentorPending = role === 'MENTOR' && user.verification_status !== 'VERIFIED';
  return (
    <div className="min-h-screen flex" style={{ '--accent': ACCENT[role] }}>
      <aside className={cn('hidden lg:block bg-white border-r border-black/5 sticky top-0 h-screen shrink-0 transition-all', collapsed ? 'w-[76px]' : 'w-[256px]')}><Sidebar role={role} collapsed={collapsed} /></aside>
      {drawer && <div className="fixed inset-0 z-40 lg:hidden"><div className="absolute inset-0 bg-indigo2/40" onClick={() => setDrawer(false)} /><div className="relative w-72 h-full bg-white"><button className="absolute top-4 right-3 p-1" onClick={() => setDrawer(false)} aria-label="Close menu"><X size={20} /></button><Sidebar role={role} onNavigate={() => setDrawer(false)} /></div></div>}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-16 bg-white/80 backdrop-blur border-b border-black/5 flex items-center justify-between px-4 md:px-8 sticky top-0 z-30">
          <div className="flex items-center gap-2 min-w-0">
            <button className="lg:hidden p-2 rounded-xl hover:bg-pale" onClick={() => setDrawer(true)} aria-label="Open menu"><Menu size={20} /></button>
            <button className="hidden lg:block p-2 rounded-xl hover:bg-pale" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar">{collapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}</button>
            <div className="text-sm truncate"><span className="font-semibold text-accent capitalize">{role.toLowerCase()} portal</span>{current && <span className="text-gray-400"> / {current[1]}</span>}</div>
          </div>
          <div className="flex items-center gap-2">
            <NotificationBell role={role} />
            <div className="relative">
              <button onClick={() => setMenu(!menu)} className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-xl hover:bg-pale"><Avatar name={user.name} size={32} /><span className="hidden sm:block text-sm font-medium max-w-32 truncate">{user.name}</span><ChevronDown size={14} /></button>
              {menu && <div className="absolute right-0 mt-2 w-44 bg-white rounded-card shadow-2xl border border-black/5 py-1 z-40 text-sm">
                {role !== 'ADMIN' && <Link className="block px-4 py-2 hover:bg-pale" to={`/${role.toLowerCase()}/profile`}>My profile</Link>}
                <Link className="block px-4 py-2 hover:bg-pale" to={`/${role.toLowerCase()}/settings`}>Settings</Link>
                <button className="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50" onClick={() => { logout(); nav('/'); }}>Logout</button></div>}
            </div>
          </div>
        </header>
        <main className="p-4 md:p-8 max-w-7xl w-full mx-auto">
          {mentorPending && <div className="mb-6 rounded-card bg-amber-50 border border-amber-200 text-amber-900 text-sm p-4">Your mentor account is <b>{user.verification_status.toLowerCase()}</b>. Students can discover you once an administrator verifies your profile. Complete your profile to speed this up.</div>}
          <Outlet />
        </main>
      </div>
    </div>
  );
}
