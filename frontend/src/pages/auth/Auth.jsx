import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { useAuth } from '../../hooks/useAuth';
import { HOME } from '../../config/nav';
import { Button, Card, Field, Input, Select, cn } from '../../components/ui';
import { Logo } from '../../components/layout/PublicLayout';

const Shell = ({ title, sub, children }) => <div className="hero-bg min-h-screen flex items-center justify-center p-4"><div className="w-full max-w-md"><Link to="/" className="flex justify-center mb-6"><Logo /></Link><Card className="p-7"><h1 className="text-2xl font-extrabold">{title}</h1><p className="text-sm text-gray-500 mt-1 mb-5">{sub}</p>{children}</Card></div></div>;
const DEMO = [['Student', 'student@rockstarz.dev'], ['Mentor', 'mentor@rockstarz.dev'], ['Admin', 'admin@rockstarz.dev']];

export function Login() {
  const { user, login } = useAuth(); const nav = useNavigate(); const loc = useLocation(); const [busy, setBusy] = useState(false);
  const f = useForm({ resolver: zodResolver(z.object({ email: z.string().email('Enter a valid email'), password: z.string().min(6, 'At least 6 characters') })), defaultValues: { email: '', password: '' } });
  if (user) return <Navigate to={HOME[user.role]} replace />;
  const submit = async ({ email, password }) => { setBusy(true); try { const u = await login(email, password); nav(loc.state?.from?.startsWith(`/${u.role.toLowerCase()}`) ? loc.state.from : HOME[u.role], { replace: true }); } catch (e) { toast.error(e.message); } finally { setBusy(false); } };
  return (
    <Shell title="Welcome back" sub="Log in to continue your mentoring journey.">
      <form onSubmit={f.handleSubmit(submit)} className="grid gap-4" noValidate>
        <Field label="Email" error={f.formState.errors.email?.message}><Input type="email" autoComplete="email" {...f.register('email')} /></Field>
        <Field label="Password" error={f.formState.errors.password?.message}><Input type="password" autoComplete="current-password" {...f.register('password')} /></Field>
        <Button type="submit" loading={busy} className="w-full">Login</Button>
      </form>
      <div className="mt-5 p-3 rounded-xl bg-pale/60 text-xs"><b>Demo accounts</b> (password <span className="mono">demo123</span>) <div className="flex gap-2 mt-2">{DEMO.map(([r, e]) => <button key={r} type="button" onClick={() => { f.setValue('email', e); f.setValue('password', 'demo123'); }} className="px-3 py-1.5 rounded-lg bg-white border font-semibold hover:bg-white/70">{r}</button>)}</div></div>
      <p className="text-sm text-center mt-4">New here? <Link to="/register" className="text-brand font-semibold">Create an account</Link></p>
    </Shell>
  );
}

const schema = z.object({ role: z.enum(['STUDENT', 'MENTOR']), name: z.string().min(2, 'Enter your name'), email: z.string().email('Enter a valid email'), password: z.string().min(6, 'At least 6 characters'), confirm: z.string(), roll_number: z.string().optional(), career_objective: z.string().optional(), mentor_type: z.string().optional() })
  .refine((d) => d.password === d.confirm, { path: ['confirm'], message: 'Passwords do not match' })
  .refine((d) => d.role !== 'STUDENT' || (d.roll_number || '').trim().length >= 4, { path: ['roll_number'], message: 'Enter your roll number' });
export function Register() {
  const { user, register: signUp } = useAuth(); const nav = useNavigate(); const [sp] = useSearchParams(); const [busy, setBusy] = useState(false);
  const f = useForm({ resolver: zodResolver(schema), defaultValues: { role: sp.get('role') === 'MENTOR' ? 'MENTOR' : 'STUDENT', career_objective: 'CAREER_CLARITY', mentor_type: 'Industry Professional' } });
  const role = f.watch('role');
  if (user) return <Navigate to={HOME[user.role]} replace />;
  const submit = async ({ confirm, ...d }) => { setBusy(true); try { const u = await signUp(d); toast.success(u.role === 'MENTOR' ? 'Account created. Complete your profile for verification.' : 'Account created. Complete your profile to get matched.'); nav(`/${u.role.toLowerCase()}/profile`, { replace: true }); } catch (e) { toast.error(e.message); } finally { setBusy(false); } };
  const e = f.formState.errors;
  return (
    <Shell title="Create your account" sub="Join the Rock Starz mentoring community.">
      <div className="grid grid-cols-2 gap-2 mb-4" role="radiogroup" aria-label="Role">{[['STUDENT', 'I need guidance'], ['MENTOR', 'I want to mentor']].map(([v, t]) => <button key={v} type="button" role="radio" aria-checked={role === v} onClick={() => f.setValue('role', v)} className={cn('h-11 rounded-xl border text-sm font-semibold', role === v ? 'bg-brand text-white border-brand' : 'bg-white hover:bg-pale')}>{t}</button>)}</div>
      <form onSubmit={f.handleSubmit(submit)} className="grid gap-4" noValidate>
        <Field label="Full name" error={e.name?.message}><Input {...f.register('name')} /></Field>
        <Field label="Email" error={e.email?.message}><Input type="email" {...f.register('email')} /></Field>
        {role === 'STUDENT' ? <>
          <Field label="Roll number" error={e.roll_number?.message}><Input placeholder="e.g. 24F2000101" {...f.register('roll_number')} /></Field>
          <Field label="What are you looking for?"><Select {...f.register('career_objective')}><option value="PLACEMENT">Placements</option><option value="HIGHER_STUDIES">Higher studies</option><option value="ENTREPRENEURSHIP">Entrepreneurship</option><option value="CAREER_CLARITY">I need career clarity</option></Select></Field></>
          : <Field label="Mentor type" hint="Mentor accounts are verified by the programme team."><Select {...f.register('mentor_type')}>{['Recent Graduate', 'Industry Professional', 'Research Mentor', 'Entrepreneur', 'Faculty'].map((t) => <option key={t}>{t}</option>)}</Select></Field>}
        <div className="grid grid-cols-2 gap-3"><Field label="Password" error={e.password?.message}><Input type="password" {...f.register('password')} /></Field><Field label="Confirm" error={e.confirm?.message}><Input type="password" {...f.register('confirm')} /></Field></div>
        <Button type="submit" loading={busy} className="w-full">Create account</Button>
      </form>
      <p className="text-sm text-center mt-4">Already registered? <Link to="/login" className="text-brand font-semibold">Login</Link></p>
    </Shell>
  );
}
