import { useState } from 'react'
import { Button, Label } from './ui'
import { isoToLocalInput, localInputToIso } from '../lib/format'
import { DateTimeField } from './DateTimeField'
import type { Commitment, CommitmentCreate } from '../types'

export function CommitmentForm({
  initial,
  submitting,
  onSubmit,
  submitLabel = 'Save',
}: {
  initial?: Commitment
  submitting?: boolean
  onSubmit: (payload: CommitmentCreate) => void
  submitLabel?: string
}) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [deadline, setDeadline] = useState(isoToLocalInput(initial?.deadline))
  const [effort, setEffort] = useState(String(initial?.est_effort_minutes ?? 60))
  const [importance, setImportance] = useState(String(initial?.importance ?? 3))
  const [stakeholder, setStakeholder] = useState(initial?.stakeholder ?? '')
  const [mvd, setMvd] = useState(initial?.min_viable_definition ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')

  const valid = title.trim().length > 0 && deadline.length > 0

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault()
        if (!valid) return
        onSubmit({
          title: title.trim(),
          deadline: localInputToIso(deadline),
          est_effort_minutes: Math.max(1, Number(effort) || 60),
          importance: Math.min(5, Math.max(1, Number(importance) || 3)),
          stakeholder: stakeholder.trim() || null,
          min_viable_definition: mvd.trim() || null,
          description: description.trim() || null,
        })
      }}
    >
      <div>
        <Label>Title</Label>
        <input className="field" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="What is due?" autoFocus />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label>Deadline</Label>
          <DateTimeField value={deadline} onChange={setDeadline} />
        </div>
        <div>
          <Label>Effort (min)</Label>
          <input type="number" min={1} className="field" value={effort} onChange={(e) => setEffort(e.target.value)} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label>Importance</Label>
          <select className="field" value={importance} onChange={(e) => setImportance(e.target.value)}>
            <option value="1">1 · Trivial</option>
            <option value="2">2 · Low</option>
            <option value="3">3 · Normal</option>
            <option value="4">4 · High</option>
            <option value="5">5 · Critical</option>
          </select>
        </div>
        <div>
          <Label>Stakeholder</Label>
          <input className="field" value={stakeholder} onChange={(e) => setStakeholder(e.target.value)} placeholder="Who is waiting?" />
        </div>
      </div>
      <div>
        <Label>Minimum viable version</Label>
        <input className="field" value={mvd} onChange={(e) => setMvd(e.target.value)} placeholder="What counts as 'good enough'?" />
      </div>
      <div>
        <Label>Notes</Label>
        <textarea className="field min-h-[72px] resize-y" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <div className="flex justify-end">
        <Button type="submit" variant="ember" loading={submitting} disabled={!valid}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
