import { useState } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../../hooks/useAuth';
import { Button, Card, Field, Input, Switch } from '../../components/ui';
import { PageHeader } from '../../components/common/PageHeader';
import { authService } from '../../services/authService';
import { act } from '../../lib/utils';

export default function Settings() {
  const { user, refresh, logout } = useAuth(); const [name, setName] = useState(user.name); const [pw, setPw] = useState({ c: '', n: '' });
  return (
    <>
      <PageHeader title="Settings" sub="Account preferences." />
      <div className="grid gap-5 max-w-2xl">
        <Card><h2 className="font-bold mb-3">Account</h2><div className="grid gap-3"><Field label="Full name"><Input value={name} onChange={(e) => setName(e.target.value)} /></Field><Field label="Email"><Input value={user.email} disabled /></Field><Button className="justify-self-start" disabled={name.trim().length < 2} onClick={async () => { if (await act(() => authService.updateMe({ name }), 'Account updated')) refresh(); }}>Save</Button></div></Card>
        <Card><h2 className="font-bold mb-3">Notifications</h2><div className="flex items-center justify-between gap-4"><div><div className="text-sm font-medium">Email notifications</div><div className="text-xs text-gray-500">In-app notifications are always on. Email is not available in this prototype.</div></div><Switch label="Email notifications" checked={!!user.settings?.email_notifications} onChange={async (v) => { if (await act(() => authService.updateMe({ settings: { email_notifications: v } }))) refresh(); }} /></div></Card>
        <Card><h2 className="font-bold mb-3">Change password</h2><div className="grid gap-3"><Field label="Current password"><Input type="password" value={pw.c} onChange={(e) => setPw({ ...pw, c: e.target.value })} /></Field><Field label="New password"><Input type="password" value={pw.n} onChange={(e) => setPw({ ...pw, n: e.target.value })} /></Field><Button className="justify-self-start" disabled={!pw.c || pw.n.length < 6} onClick={async () => { if (await act(() => authService.changePassword(pw.c, pw.n), 'Password changed')) setPw({ c: '', n: '' }); }}>Update password</Button></div></Card>
        <Card className="border-dashed"><h2 className="font-bold mb-1">Demo data</h2><p className="text-sm text-gray-500 mb-3">Sample data is stored in your browser. Reset to restore the original dataset.</p><Button variant="dangerOutline" onClick={async () => { await authService.resetDemo(); toast.success('Demo data reset'); logout(); }}>Reset demo data</Button></Card>
      </div>
    </>
  );
}
