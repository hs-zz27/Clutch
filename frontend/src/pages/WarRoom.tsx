import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { Shell } from '../components/Shell'
import { CountdownClock } from '../components/CountdownClock'
import { CommitmentsPanel } from '../components/CommitmentsPanel'
import { PlanTimeline } from '../components/PlanTimeline'
import { AgentConsole } from '../components/AgentConsole'
import { CapacityPanel } from '../components/CapacityPanel'
import { RenegotiationOutbox } from '../components/RenegotiationOutbox'
import { KnowledgePanel } from '../components/KnowledgePanel'
import { Stat } from '../components/ui'
import { ClutchApi } from '../api'
import { formatMinutes } from '../lib/format'

export default function WarRoom() {
  const commitments = useQuery({ queryKey: ['commitments'], queryFn: ClutchApi.listCommitments })
  const plan = useQuery({ queryKey: ['plan'], queryFn: ClutchApi.plan, refetchInterval: 30_000 })

  const active = (commitments.data ?? []).filter((c) => c.status !== 'done' && c.status !== 'dropped')
  const nextDeadline = active
    .map((c) => c.deadline)
    .sort((a, b) => new Date(a).getTime() - new Date(b).getTime())[0]

  const feasible = plan.data?.feasible ?? true
  const deficit = plan.data?.total_deficit_minutes ?? 0

  return (
    <Shell>
      {/* hero / situation board */}
      <section className="panel rail-ember reveal mb-5 overflow-hidden">
        <div className="grid items-center gap-5 p-5 md:grid-cols-[1fr_auto]">
          <div>
            <div className="mb-1 font-mono text-xs uppercase tracking-[0.24em] text-faint">situation board</div>
            <h1 className="font-display text-3xl font-700 tracking-tight">War Room</h1>
            <p className="mt-1 max-w-md text-sm text-muted">
              Everything you owe, the time you actually have, and the agent's call on what to do next.
            </p>
            <div className="mt-4 grid grid-cols-3 gap-3">
              <Stat value={active.length} label="active" />
              <Stat value={plan.data?.schedule.length ?? 0} label="scheduled" />
              <Stat
                value={feasible ? <span className="inline-flex items-center gap-1"><CheckCircle2 className="h-5 w-5" />ok</span> : formatMinutes(deficit)}
                label={feasible ? 'status' : 'short by'}
                tone={feasible ? 'teal' : 'coral'}
              />
            </div>
          </div>
          <div className="flex flex-col items-start gap-2 md:items-end">
            {nextDeadline ? (
              <CountdownClock target={nextDeadline} label="next deadline" className="md:items-end" />
            ) : (
              <div className="flex items-center gap-2 text-muted"><CheckCircle2 className="h-5 w-5 text-teal" /> nothing due</div>
            )}
            {!feasible && (
              <span className="flex items-center gap-1 font-mono text-xs text-coral">
                <AlertTriangle className="h-3.5 w-3.5" /> over capacity — triage now
              </span>
            )}
          </div>
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[1.55fr_1fr]">
        <div className="space-y-5 stagger">
          <CommitmentsPanel />
          <PlanTimeline />
          <AgentConsole />
        </div>
        <div className="space-y-5 stagger">
          <CapacityPanel />
          <RenegotiationOutbox />
          <KnowledgePanel />
        </div>
      </div>
    </Shell>
  )
}
