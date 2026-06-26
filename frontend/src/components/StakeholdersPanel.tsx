import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2, Users } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, Chip, EmptyState, ErrorNote, Label, Modal, Panel, Spinner } from './ui'
import type { Stakeholder, StakeholderCreate } from '../types'

function StakeholderForm({
  initial,
  submitting,
  onSubmit,
}: {
  initial?: Stakeholder
  submitting?: boolean
  onSubmit: (payload: StakeholderCreate) => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [relationship, setRelationship] = useState(initial?.relationship ?? '')
  const [formality, setFormality] = useState(String(initial?.formality ?? 3))
  const [notes, setNotes] = useState(initial?.notes ?? '')

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault()
        if (!name.trim()) return
        onSubmit({
          name: name.trim(),
          relationship: relationship.trim() || null,
          formality: Number(formality),
          notes: notes.trim() || null,
        })
      }}
    >
      <div>
        <Label>Name</Label>
        <input className="field" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Jane Doe, Investors" autoFocus />
      </div>
      <div>
        <Label>Relationship context</Label>
        <input className="field" value={relationship} onChange={(e) => setRelationship(e.target.value)} placeholder="e.g. Boss, Key Client, Vendor" />
      </div>
      <div>
        <Label>Formality level (1-5)</Label>
        <select className="field" value={formality} onChange={(e) => setFormality(e.target.value)}>
          <option value="1">1 · Very casual</option>
          <option value="2">2 · Casual</option>
          <option value="3">3 · Professional</option>
          <option value="4">4 · Formal</option>
          <option value="5">5 · Extremely formal / Legal</option>
        </select>
        <div className="mt-1 text-xs text-faint">Guides the tone of agent-drafted renegotiations.</div>
      </div>
      <div>
        <Label>Notes / quirks</Label>
        <textarea className="field min-h-[64px] resize-y" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. Hates long emails, prefers bullet points." />
      </div>
      <div className="flex justify-end pt-2">
        <Button type="submit" variant="ember" loading={submitting} disabled={!name.trim()}>Save</Button>
      </div>
    </form>
  )
}

export function StakeholdersPanel() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [editing, setEditing] = useState<Stakeholder | null>(null)

  const list = useQuery({ queryKey: ['stakeholders'], queryFn: ClutchApi.listStakeholders })
  const create = useMutation({
    mutationFn: (p: StakeholderCreate) => ClutchApi.createStakeholder(p),
    onSuccess: () => { setShowCreate(false); qc.invalidateQueries({ queryKey: ['stakeholders'] }) },
  })
  const update = useMutation({
    mutationFn: ({ id, p }: { id: number; p: StakeholderCreate }) => ClutchApi.updateStakeholder(id, p),
    onSuccess: () => { setEditing(null); qc.invalidateQueries({ queryKey: ['stakeholders'] }) },
  })
  const remove = useMutation({
    mutationFn: (id: number) => ClutchApi.deleteStakeholder(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['stakeholders'] }),
  })

  return (
    <Panel
      title="Stakeholders"
      icon={<Users className="h-4 w-4 text-ember" />}
      rail="teal"
      actions={
        <Button variant="ghost" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" /> Add
        </Button>
      }
    >
      {list.isLoading ? (
        <div className="flex justify-center py-6"><Spinner /></div>
      ) : list.isError ? (
        <ErrorNote>Could not load stakeholders.</ErrorNote>
      ) : !list.data || list.data.length === 0 ? (
        <EmptyState icon={<Users className="h-6 w-6" />} title="No stakeholders defined" hint="Add the people you owe commitments to so the agent can draft pushback." />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {list.data.map((s) => (
            <li key={s.id} className="rounded-lg border border-line-soft bg-surface-2 p-3">
              <div className="flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <div className="truncate font-display font-700">{s.name}</div>
                  <div className="mt-1 flex items-center gap-2">
                    {s.relationship && <span className="text-xs text-muted">{s.relationship}</span>}
                    <Chip tone="muted">Formality {s.formality}</Chip>
                  </div>
                  {s.notes && <p className="mt-2 text-xs text-faint line-clamp-2">{s.notes}</p>}
                </div>
                <div className="ml-2 flex shrink-0 flex-col gap-1">
                  <button className="btn btn-ghost px-2 py-1" title="Edit" onClick={() => setEditing(s)}><Pencil className="h-3 w-3" /></button>
                  <button className="btn btn-ghost px-2 py-1" title="Delete" onClick={() => remove.mutate(s.id)}><Trash2 className="h-3 w-3" /></button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New stakeholder">
        {create.isError && <div className="mb-3"><ErrorNote>{(create.error as ApiError)?.detail ?? 'Could not create.'}</ErrorNote></div>}
        <StakeholderForm submitting={create.isPending} onSubmit={(p) => create.mutate(p)} />
      </Modal>

      <Modal open={!!editing} onClose={() => setEditing(null)} title="Edit stakeholder">
        {editing && (
          <>
            {update.isError && <div className="mb-3"><ErrorNote>{(update.error as ApiError)?.detail ?? 'Could not update.'}</ErrorNote></div>}
            <StakeholderForm initial={editing} submitting={update.isPending} onSubmit={(p) => update.mutate({ id: editing.id, p })} />
          </>
        )}
      </Modal>
    </Panel>
  )
}
