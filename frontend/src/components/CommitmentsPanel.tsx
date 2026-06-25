import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ListTodo, Pencil, Plus, Sparkles, Trash2, Wand2 } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, Chip, EmptyState, ErrorNote, Label, Modal, Panel, Spinner } from './ui'
import { CommitmentForm } from './CommitmentForm'
import { STATUS_META, IMPORTANCE_LABEL } from '../lib/meta'
import { cx, formatMinutes, relativeDeadline } from '../lib/format'
import type { Commitment, CommitmentCreate, CommitmentStatus } from '../types'

const STATUS_OPTIONS: CommitmentStatus[] = ['not_started', 'in_progress', 'done', 'deferred', 'dropped']

export function CommitmentsPanel() {
  const qc = useQueryClient()
  const [nlText, setNlText] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editing, setEditing] = useState<Commitment | null>(null)

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['commitments'] })
    qc.invalidateQueries({ queryKey: ['plan'] })
    qc.invalidateQueries({ queryKey: ['capacity'] })
  }

  const list = useQuery({ queryKey: ['commitments'], queryFn: ClutchApi.listCommitments })

  const parse = useMutation({
    mutationFn: (text: string) => ClutchApi.parseCommitments(text),
    onSuccess: () => {
      setNlText('')
      refresh()
    },
  })
  const create = useMutation({
    mutationFn: (p: CommitmentCreate) => ClutchApi.createCommitment(p),
    onSuccess: () => {
      setShowCreate(false)
      refresh()
    },
  })
  const update = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Parameters<typeof ClutchApi.updateCommitment>[1] }) =>
      ClutchApi.updateCommitment(id, payload),
    onSuccess: () => {
      setEditing(null)
      refresh()
    },
  })
  const remove = useMutation({
    mutationFn: (id: number) => ClutchApi.deleteCommitment(id),
    onSuccess: refresh,
  })

  const rows = [...(list.data ?? [])].sort(
    (a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime(),
  )

  return (
    <Panel
      title="Commitments"
      icon={<ListTodo className="h-4 w-4 text-ember" />}
      rail="ember"
      actions={
        <Button variant="ghost" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" /> Add
        </Button>
      }
    >
      {/* natural-language capture */}
      <div className="mb-4 rounded-lg border border-line-soft bg-ink-2 p-3">
        <Label>Brain dump</Label>
        <textarea
          className="field min-h-[64px] resize-y"
          placeholder="e.g. Send the investor update by Friday 5pm, polish the demo deck tonight, reply to the vendor RFP sometime this week…"
          value={nlText}
          onChange={(e) => setNlText(e.target.value)}
        />
        <div className="mt-2 flex items-center justify-between">
          <span className="flex items-center gap-1 font-mono text-xs text-faint">
            <Sparkles className="h-3 w-3 text-ember" /> parsed by Gemini into structured commitments
          </span>
          <Button
            variant="ember"
            loading={parse.isPending}
            disabled={!nlText.trim()}
            onClick={() => parse.mutate(nlText.trim())}
          >
            <Wand2 className="h-4 w-4" /> Parse
          </Button>
        </div>
        {parse.isError && <div className="mt-2"><ErrorNote>{(parse.error as ApiError)?.detail ?? 'Could not parse text.'}</ErrorNote></div>}
      </div>

      {list.isLoading ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : list.isError ? (
        <ErrorNote>Could not load commitments. Is the backend running?</ErrorNote>
      ) : rows.length === 0 ? (
        <EmptyState icon={<ListTodo className="h-6 w-6" />} title="Nothing tracked yet" hint="Brain-dump above or add a commitment manually." />
      ) : (
        <ul className="space-y-2">
          {rows.map((c) => {
            const sm = STATUS_META[c.status]
            const closed = c.status === 'done' || c.status === 'dropped'
            return (
              <li key={c.id} className="rounded-lg border border-line-soft bg-ink-2 px-3 py-2.5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className={cx('truncate font-600', closed && 'text-faint line-through')}>{c.title}</div>
                    <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-xs text-faint">
                      <span className={cx(new Date(c.deadline).getTime() < Date.now() && !closed && 'text-coral')}>
                        {relativeDeadline(c.deadline)}
                      </span>
                      <span>{formatMinutes(c.est_effort_minutes)} effort</span>
                      <span>{c.progress_pct}% done</span>
                      {c.stakeholder && <span className="text-muted">@{c.stakeholder}</span>}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    <Chip tone={c.importance >= 4 ? 'coral' : 'muted'}>{IMPORTANCE_LABEL[c.importance] ?? `P${c.importance}`}</Chip>
                    <Chip tone={sm.tone}>{sm.label}</Chip>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <select
                    className="field max-w-[150px] py-1 text-xs"
                    value={c.status}
                    onChange={(e) => update.mutate({ id: c.id, payload: { status: e.target.value as CommitmentStatus } })}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{STATUS_META[s].label}</option>
                    ))}
                  </select>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    step={5}
                    defaultValue={c.progress_pct}
                    className="h-1 flex-1 cursor-pointer accent-ember"
                    onMouseUp={(e) => update.mutate({ id: c.id, payload: { progress_pct: Number((e.target as HTMLInputElement).value) } })}
                    onTouchEnd={(e) => update.mutate({ id: c.id, payload: { progress_pct: Number((e.target as HTMLInputElement).value) } })}
                  />
                  <button className="btn btn-ghost px-2 py-1" title="Edit" onClick={() => setEditing(c)}>
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button className="btn btn-ghost px-2 py-1" title="Delete" onClick={() => remove.mutate(c.id)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </li>
            )
          })}
        </ul>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New commitment">
        {create.isError && <div className="mb-3"><ErrorNote>{(create.error as ApiError)?.detail ?? 'Could not create.'}</ErrorNote></div>}
        <CommitmentForm submitting={create.isPending} submitLabel="Add commitment" onSubmit={(p) => create.mutate(p)} />
      </Modal>

      <Modal open={!!editing} onClose={() => setEditing(null)} title="Edit commitment">
        {editing && (
          <>
            {update.isError && <div className="mb-3"><ErrorNote>{(update.error as ApiError)?.detail ?? 'Could not update.'}</ErrorNote></div>}
            <CommitmentForm
              initial={editing}
              submitting={update.isPending}
              submitLabel="Save changes"
              onSubmit={(p) => update.mutate({ id: editing.id, payload: p })}
            />
          </>
        )}
      </Modal>
    </Panel>
  )
}
