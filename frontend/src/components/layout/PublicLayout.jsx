import { useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { Menu, Star, X } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { HOME } from '../../config/nav';
import { Button, cn } from '../ui';

export const Logo = ({ compact }) => (
  <span className="inline-flex items-center gap-2"><span className="w-9 h-9 rounded-xl bg-brand text-ivory flex items-center justify-center"><Star size={18} fill="currentColor" /></span>{!compact && <span className="font-head font-extrabold tracking-wide text-indigo2">ROCK STARZ</span>}</span>
);
const links = [['/', 'Home'], ['/explore', 'Explore Mentors'], ['/how-it-works', 'How It Works'], ['/about', 'About']];
export default function PublicLayout() {
  const { user } = useAuth(); const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-30 glass !border-x-0 !border-t-0">
        <div className="max-w-7xl mx-auto h-16 px-4 md:px-8 flex items-center justify-between">
          <Link to="/"><Logo /></Link>
          <nav className="hidden md:flex items-center gap-1" aria-label="Main">{links.map(([to, t]) => <NavLink key={to} to={to} end className={({ isActive }) => cn('px-3 py-2 rounded-lg text-sm font-medium hover:bg-pale', isActive && 'text-brand bg-pale')}>{t}</NavLink>)}</nav>
          <div className="hidden md:flex gap-2">{user ? <Link to={HOME[user.role]}><Button size="sm">Go to dashboard</Button></Link> : <><Link to="/login"><Button size="sm" variant="ghost">Login</Button></Link><Link to="/register"><Button size="sm">Get Started</Button></Link></>}</div>
          <button className="md:hidden p-2" onClick={() => setOpen(!open)} aria-label="Menu">{open ? <X /> : <Menu />}</button>
        </div>
        {open && <div className="md:hidden px-4 pb-4 grid gap-1">{links.map(([to, t]) => <Link key={to} to={to} onClick={() => setOpen(false)} className="px-3 py-2 rounded-lg hover:bg-pale">{t}</Link>)}<Link to="/login" onClick={() => setOpen(false)} className="px-3 py-2">Login</Link><Link to="/register" onClick={() => setOpen(false)}><Button className="w-full">Get Started</Button></Link></div>}
      </header>
      <main className="flex-1"><Outlet /></main>
      <footer className="bg-indigo2 text-white/80 mt-16">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-10 grid gap-8 md:grid-cols-4 text-sm">
          <div className="md:col-span-2"><div className="font-head font-extrabold text-white text-lg mb-2">ROCK STARZ</div><p className="max-w-sm">A mentorship, guidance and professional-development platform for IITM BS students. Find guidance. Build your future.</p></div>
          <div><div className="font-semibold text-white mb-2">Platform</div><div className="grid gap-1"><Link to="/explore">Explore mentors</Link><Link to="/how-it-works">How it works</Link><Link to="/about">About</Link></div></div>
          <div><div className="font-semibold text-white mb-2">Help</div><div className="grid gap-1"><span>Contact: team-046@rockstarz.dev</span><span>Privacy: admins see aggregate data only</span><span>Policies (sample)</span></div></div>
        </div>
        <div className="border-t border-white/10 text-center text-xs py-4">© 2026 Rock Starz · SE-SEP2026-Team-046 · Prototype with sample data</div>
      </footer>
    </div>
  );
}
