import { useState } from 'react';
import { Inbox as InboxIcon } from 'lucide-react';
import { ConfirmationDialog, Tabs, Textarea } from '../../components/ui';
import { RequestCard } from '../../components/common/Cards';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState, Load } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { requestService } from '../../services/requestService';
import { act } from '../../lib/utils';

export default function RequestInbox() {
  const q = useAsync(requestService.list, []); const [tab, setTab] = useState('PENDING'); const [rej, setRej] = useState(null); const [reason, setReason] = useState(''); const [busy, setBusy] = useState(false);
  const groups = { PENDING: ['PENDING'], ACCEPTED: ['ACCEPTED'], CLOSED: ['REJECTED', 'EXPIRED', 'CANCELLED'] };
  const run = async (fn, ok) => { setBusy(true); const r = await act(fn, ok); setBusy(false); if (r) q.reload(); return r; };
  return (
    <>
      <PageHeader title="Request inbox" sub="Review mentoring requests. Unanswered requests expire after 48 hours." />
      <Load q={q} rows={3} className="h-40">{(all) => {
        const by = (k) => all.filter((r) => groups[k].includes(r.status)); const list = by(tab);
        return (<>
          <Tabs value={tab} onChange={setTab} tabs={[{ id: 'PENDING', label: 'Pending', count: by('PENDING').length }, { id: 'ACCEPTED', label: 'Accepted', count: by('ACCEPTED').length }, { id: 'CLOSED', label: 'Rejected / Expired', count: by('CLOSED').length }]} />
          <div className="mt-4 grid gap-4 lg:grid-cols-2">{list.length ? list.map((r) => <RequestCard key={r.id} r={r} busy={busy} onAccept={(x) => run(() => requestService.accept(x.id), `Accepted. ${x.student.name} is now your mentee.`)} onReject={(x) => { setReason(''); setRej(x); }} />) : <div className="lg:col-span-2"><EmptyState icon={InboxIcon} title="Nothing here" text="Requests will appear in this tab." /></div>}</div>
        </>);
      }}</Load>
      <ConfirmationDialog open={!!rej} onClose={() => setRej(null)} danger loading={busy} title="Reject this request?" text={`${rej?.student.name} will be notified and can try another mentor.`} confirmLabel="Reject request" onConfirm={async () => { const id = rej.id; if (await run(() => requestService.reject(id, reason), 'Request rejected')) setRej(null); }}>
        <Textarea className="!h-20" placeholder="Reason (optional, shared with the student)" value={reason} onChange={(e) => setReason(e.target.value)} />
      </ConfirmationDialog>
    </>
  );
}
