import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Beaker, EyeOff, Plus, Trash2 } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, Chip, ErrorNote, Label, Panel, Spinner } from './ui'
import { cx, formatMinutes } from '../lib/format'

export function WhatIfPanel() {
  const [drops, setDrops] = useState<number[]>([])
  const [extraFocus, setExtraFocus] = useState('')

  const commitments = useQuery({ queryKey: ['commitments'], queryFn: ClutchApi.listCommitments })
  const active = (commitments.data ?? []).filter((c) => c.status !== 'done' && c.status !== 'dropped')

  const sim = useMutation({
    mutationFn: () => ClutchApi.runWhatIf({
      drop_ids: drops,
      extra_focus_minutes: extraFocus ? Number(extraFocus) : undefined,
    }),
  })

  const toggleDrop = (id: number) => {
    setDrops((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])
  }

  return (
    <Panel
      title="What-If Simulator"
      icon={<Beaker className="h-4 w-4 text-ember" />}
      rail="iris"
      actions={
        <Button variant="ember" loading={sim.isPending} onClick={() => sim.mutate()}>
          Run scenario
        </Button>
      }
    >
      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-4">
          <p className="text-sm text-muted">
            Experiment with dropping tasks or pulling all-nighters without actually wrecking your active plan.
          </p>

          <div>
            <Label>Extra focus time (e.g. skip sleep)</Label>
            <div className="flex items-center gap-2">
              <Plus className="h-4 w-4 text-faint" />
              <input type="number" className="field w-24" placeholder="mins" value={extraFocus} onChange={(e) => setExtraFocus(e.target.value)} />
              <span className="text-sm text-muted">minutes added to capacity</span>
            </div>
          </div>

          <div>
            <Label>Tasks to drop (simulate failure)</Label>
            {commitments.isLoading ? (
              <Spinner />
            ) : (
              <div className="space-y-1.5 max-h-[250px] overflow-y-auto pr-2">
                {active.map((c) => {
                  const isDropped = drops.includes(c.id)
                  return (
                    <label key={c.id} className={cx(
                      "flex cursor-pointer items-center justify-between rounded-lg border px-3 py-2 transition-colors",
                      isDropped ? "border-coral bg-coral/10 text-coral" : "border-line-soft bg-surface-2 hover:border-line"
                    )}>
                      <span className="truncate text-sm font-600">{c.title}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs opacity-70">{formatMinutes(c.est_effort_minutes)}</span>
                        <input
                          type="checkbox"
                          className="h-4 w-4 accent-coral"
                          checked={isDropped}
                          onChange={() => toggleDrop(c.id)}
                        />
                      </div>
                    </label>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border-2 border-line bg-ink-2 p-4">
          <div className="mb-3"><Label>Simulation results</Label></div>

          {!sim.data && !sim.isPending && !sim.isError && (
            <div className="flex h-32 flex-col items-center justify-center text-faint">
              <EyeOff className="mb-2 h-6 w-6" />
              <span className="text-sm">Run a scenario to see the impact.</span>
            </div>
          )}

          {sim.isPending && (
            <div className="flex h-32 items-center justify-center"><Spinner /></div>
          )}

          {sim.isError && (
            <ErrorNote>{(sim.error as ApiError)?.detail ?? 'Simulation failed.'}</ErrorNote>
          )}

          {sim.data && (
            <div className="space-y-4 reveal">
              <div className="flex items-center justify-between border-b border-line-soft pb-3">
                <span className="text-sm font-600 text-muted">Feasibility</span>
                <div className="flex items-center gap-2">
                  <Chip tone={sim.data.diff.feasible_before ? 'teal' : 'coral'}>{sim.data.diff.feasible_before ? 'Feasible' : 'Deficit'}</Chip>
                  <span className="text-faint">→</span>
                  <Chip tone={sim.data.diff.feasible_after ? 'teal' : 'coral'}>{sim.data.diff.feasible_after ? 'Feasible' : 'Deficit'}</Chip>
                </div>
              </div>

              <div className="flex items-center justify-between border-b border-line-soft pb-3">
                <span className="text-sm font-600 text-muted">Total Deficit</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm">{formatMinutes(sim.data.diff.deficit_minutes_before)}</span>
                  <span className="text-faint">→</span>
                  <span className={cx('font-mono text-sm font-700', sim.data.diff.deficit_minutes_after < sim.data.diff.deficit_minutes_before ? 'text-teal' : 'text-coral')}>
                    {formatMinutes(sim.data.diff.deficit_minutes_after)}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pb-1">
                <span className="text-sm font-600 text-muted">Worst-case Deficit</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm">{formatMinutes(sim.data.diff.worst_case_deficit_before)}</span>
                  <span className="text-faint">→</span>
                  <span className="font-mono text-sm">{formatMinutes(sim.data.diff.worst_case_deficit_after)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Panel>
  )
}
