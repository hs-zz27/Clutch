import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarDays, CalendarSync, Gauge, Plus, Trash2, X } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, EmptyState, ErrorNote, Label, Panel, Spinner } from './ui'
import { ScrollHintPanel } from './ScrollHintPanel'
import { CapacityMeter } from './CapacityMeter'
import { DateTimeField } from './DateTimeField'
import { dayOfMonth, formatDateTime, formatTime, localInputToIso, monthShort } from '../lib/format'

export function CapacityPanel() {
  const qc = useQueryClient()
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [label, setLabel] = useState('')
  const [adding, setAdding] = useState(false)
  const [icsNote, setIcsNote] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  useEffect(() => {
    if (icsNote?.type === 'ok') {
      const timer = setTimeout(() => setIcsNote(null), 6000)
      return () => clearTimeout(timer)
    }
  }, [icsNote])

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['busy'] })
    qc.invalidateQueries({ queryKey: ['capacity'] })
    qc.invalidateQueries({ queryKey: ['plan'] })
  }

  const blocks = useQuery({ queryKey: ['busy'], queryFn: ClutchApi.listBusyBlocks })
  const capacity = useQuery({ queryKey: ['capacity'], queryFn: () => ClutchApi.capacity(), retry: false })
  const plan = useQuery({ queryKey: ['plan'], queryFn: ClutchApi.plan })

  const required = (plan.data?.schedule ?? []).reduce((sum, s) => sum + s.remaining_minutes, 0)
  const available = capacity.data?.available_minutes ?? 0

  const create = useMutation({
    mutationFn: () => ClutchApi.createBusyBlock({ start: localInputToIso(start), end: localInputToIso(end), label: label.trim() || null }),
    onSuccess: () => {
      setStart(''); setEnd(''); setLabel(''); setAdding(false)
      refresh()
    },
  })
  const remove = useMutation({ mutationFn: (id: number) => ClutchApi.deleteBusyBlock(id), onSuccess: refresh })
  const sync = useMutation({
    mutationFn: () => ClutchApi.syncIcs(),
    onSuccess: (res) => {
      setIcsNote({ type: 'ok', text: `Imported ${(res as { imported?: number }).imported ?? 0} block(s) from the calendar feed.` })
      refresh()
    },
    onError: (e) => {
      const err = e as ApiError
      setIcsNote({
        type: 'err',
        text: err.status === 503
          ? 'Calendar sync is not configured (optional ICS feature is off).'
          : err.status === 502
            ? 'Could not fetch or parse the configured calendar feed.'
            : err.detail || 'Calendar sync failed.',
      })
    },
  })

  const validBlock = start && end && localInputToIso(end) > localInputToIso(start)

  return (
    <Panel
      title="Capacity"
      icon={<Gauge className="h-4 w-4 text-ember" />}
      rail={required > available ? 'coral' : 'teal'}
      actions={
        <Button variant="ghost" loading={sync.isPending} onClick={() => { setIcsNote(null); sync.mutate() }}>
          <CalendarSync className="h-4 w-4" /> Sync ICS
        </Button>
      }
    >
      {capacity.isLoading ? (
        <div className="flex justify-center py-6"><Spinner /></div>
      ) : capacity.isError ? (
        <div className="mb-3 rounded-lg border border-line-soft bg-ink-2 px-3 py-2 text-sm text-faint">
          Add a pending commitment to compute available focus time.
        </div>
      ) : (
        <div className="mb-4 rounded-lg border border-line-soft bg-surface-2 p-3">
          <CapacityMeter available={available} required={required} />
          {capacity.data && (
            <div className="mt-2 font-mono text-[11px] text-faint">
              horizon → {formatDateTime(capacity.data.until)}
            </div>
          )}
        </div>
      )}

      {icsNote && (
        <div
          className={`mb-3 flex items-start justify-between gap-3 rounded-lg border px-3 py-2 text-sm ${
            icsNote.type === 'ok'
              ? 'border-teal/30 bg-teal/10 text-teal'
              : 'border-coral/30 bg-coral/10 text-coral'
          }`}
        >
          <div>{icsNote.text}</div>
          <button onClick={() => setIcsNote(null)} className="mt-0.5 shrink-0 opacity-70 hover:opacity-100">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="mb-3 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-sm font-600 text-muted">
          <CalendarDays className="h-4 w-4" /> Busy blocks
        </span>
        <Button variant="ghost" onClick={() => setAdding((v) => !v)}>
          <Plus className="h-4 w-4" /> Block
        </Button>
      </div>

      {adding && (
        <div className="mb-3 space-y-2 rounded-lg border border-line-soft bg-ink-2 p-3">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>Start</Label>
              <DateTimeField value={start} onChange={setStart} placeholder="Start time" />
            </div>
            <div>
              <Label>End</Label>
              <DateTimeField value={end} onChange={setEnd} placeholder="End time" />
            </div>
          </div>
          <div>
            <Label>Label</Label>
            <input className="field" placeholder="Class, sleep, commute…" value={label} onChange={(e) => setLabel(e.target.value)} />
          </div>
          {create.isError && <ErrorNote>{(create.error as ApiError)?.detail ?? 'Could not add block.'}</ErrorNote>}
          <div className="flex justify-end">
            <Button variant="ember" loading={create.isPending} disabled={!validBlock} onClick={() => create.mutate()}>Add block</Button>
          </div>
        </div>
      )}

      {blocks.isLoading ? (
        <div className="flex justify-center py-4"><Spinner /></div>
      ) : blocks.isError ? (
        <ErrorNote>Could not load busy blocks.</ErrorNote>
      ) : (blocks.data?.length ?? 0) === 0 ? (
        <EmptyState title="No busy blocks" hint="Add sleep, classes or meetings so capacity stays honest." />
      ) : (
        <ScrollHintPanel
          maxHeightClass="max-h-[220px] sm:max-h-[280px]"
          hint="Scroll to see more busy blocks"
        >
          <ul className="space-y-1.5">
            {blocks.data!.map((b) => (
              <li key={b.id} className="flex items-center gap-3 rounded-lg border border-line-soft bg-surface-2 px-3 py-2">
              <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center rounded-lg border-2 border-line bg-line pt-0.5">
                <span className="font-mono text-[9px] font-600 uppercase tracking-widest text-ember">{monthShort(b.start)}</span>
                <span className="font-display text-sm font-700 leading-none text-ink-2">{dayOfMonth(b.start)}</span>
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-600">{b.label || 'Busy'}</div>
                <div className="font-mono text-xs text-faint">{formatTime(b.start)} → {formatTime(b.end)}</div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {b.source !== 'manual' && <span className="chip border-iris/40 text-iris">{b.source}</span>}
                <button className="btn btn-ghost px-2 py-1" title="Delete" onClick={() => remove.mutate(b.id)}>
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </li>
            ))}
          </ul>
        </ScrollHintPanel>
      )}
    </Panel>
  )
}
