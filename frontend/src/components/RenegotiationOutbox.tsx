import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Mail, Send, Save, PenLine } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, Chip, EmptyState, ErrorNote, Label, Panel, Spinner } from './ui'
import { OUTBOX_META } from '../lib/meta'
import { formatDateTime } from '../lib/format'
import type { Commitment, RenegotiationMessage } from '../types'

function MessageCard({ msg, commitment }: { msg: RenegotiationMessage; commitment?: Commitment }) {
  const qc = useQueryClient()
  const [recipient, setRecipient] = useState(msg.recipient ?? '')
  const [subject, setSubject] = useState(msg.subject)
  const [body, setBody] = useState(msg.body)

  useEffect(() => {
    setRecipient(msg.recipient ?? '')
    setSubject(msg.subject)
    setBody(msg.body)
  }, [msg.id, msg.recipient, msg.subject, msg.body])

  const refresh = () => qc.invalidateQueries({ queryKey: ['renegotiations'] })
  const save = useMutation({
    mutationFn: () => ClutchApi.editRenegotiation(msg.id, { recipient: recipient.trim() || null, subject, body }),
    onSuccess: refresh,
  })
  const send = useMutation({ mutationFn: () => ClutchApi.sendRenegotiation(msg.id), onSuccess: refresh })

  const meta = OUTBOX_META[msg.status]
  const sent = msg.status === 'sent'

  return (
    <div className="rounded-lg border border-line-soft bg-ink-2 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="truncate text-sm font-600">{commitment?.title ?? `Commitment #${msg.commitment_id}`}</span>
        <Chip tone={meta.tone}>{meta.label}</Chip>
      </div>
      <div className="space-y-2">
        <div>
          <Label>To</Label>
          <input className="field py-1.5" value={recipient} disabled={sent} placeholder="name@email.com" onChange={(e) => setRecipient(e.target.value)} />
        </div>
        <div>
          <Label>Subject</Label>
          <input className="field py-1.5" value={subject} disabled={sent} onChange={(e) => setSubject(e.target.value)} />
        </div>
        <div>
          <Label>Body</Label>
          <textarea className="field min-h-[120px] resize-y py-1.5" value={body} disabled={sent} onChange={(e) => setBody(e.target.value)} />
        </div>
      </div>
      {msg.error && <div className="mt-2"><ErrorNote>{msg.error}</ErrorNote></div>}
      {(save.isError || send.isError) && (
        <div className="mt-2"><ErrorNote>{((save.error || send.error) as ApiError)?.detail ?? 'Action failed.'}</ErrorNote></div>
      )}
      <div className="mt-2 flex items-center justify-between">
        <span className="font-mono text-[11px] text-faint">
          {sent && msg.sent_at ? `sent ${formatDateTime(msg.sent_at)}` : `drafted ${formatDateTime(msg.created_at)}`}
        </span>
        {!sent && (
          <div className="flex gap-2">
            <Button variant="ghost" loading={save.isPending} onClick={() => save.mutate()}>
              <Save className="h-4 w-4" /> Save
            </Button>
            <Button variant="ember" loading={send.isPending} disabled={!recipient.trim()} onClick={() => send.mutate()}>
              <Send className="h-4 w-4" /> Send
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

export function RenegotiationOutbox() {
  const qc = useQueryClient()
  const [commitmentId, setCommitmentId] = useState('')
  const [tone, setTone] = useState('professional and apologetic')

  const messages = useQuery({ queryKey: ['renegotiations'], queryFn: ClutchApi.listRenegotiations })
  const commitments = useQuery({ queryKey: ['commitments'], queryFn: ClutchApi.listCommitments })
  const byId = new Map((commitments.data ?? []).map((c) => [c.id, c]))

  const draft = useMutation({
    mutationFn: () => ClutchApi.draftRenegotiation({ commitment_id: Number(commitmentId), tone: tone.trim() || undefined }),
    onSuccess: () => {
      setCommitmentId('')
      qc.invalidateQueries({ queryKey: ['renegotiations'] })
    },
  })

  return (
    <Panel title="Renegotiation outbox" icon={<Mail className="h-4 w-4 text-ember" />} rail="iris">
      <div className="mb-4 space-y-2 rounded-lg border border-line-soft bg-ink-2 p-3">
        <Label>Draft a deadline-extension message</Label>
        <select className="field py-1.5" value={commitmentId} onChange={(e) => setCommitmentId(e.target.value)}>
          <option value="">Select a commitment…</option>
          {(commitments.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>{c.title}{c.stakeholder ? ` · @${c.stakeholder}` : ''}</option>
          ))}
        </select>
        <input className="field py-1.5" value={tone} onChange={(e) => setTone(e.target.value)} placeholder="Tone" />
        {draft.isError && <ErrorNote>{(draft.error as ApiError)?.detail ?? 'Could not draft message.'}</ErrorNote>}
        <div className="flex justify-end">
          <Button variant="ember" loading={draft.isPending} disabled={!commitmentId} onClick={() => draft.mutate()}>
            <PenLine className="h-4 w-4" /> Draft with AI
          </Button>
        </div>
      </div>

      {messages.isLoading ? (
        <div className="flex justify-center py-6"><Spinner /></div>
      ) : messages.isError ? (
        <ErrorNote>Could not load the outbox.</ErrorNote>
      ) : (messages.data?.length ?? 0) === 0 ? (
        <EmptyState icon={<Mail className="h-6 w-6" />} title="Outbox empty" hint="Draft a message for anything you need to defer." />
      ) : (
        <div className="space-y-3">
          {messages.data!.map((m) => <MessageCard key={m.id} msg={m} commitment={byId.get(m.commitment_id)} />)}
        </div>
      )}
    </Panel>
  )
}
