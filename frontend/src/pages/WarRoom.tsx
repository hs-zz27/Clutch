import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  ListChecks,
  CalendarClock,
  Route as RouteIcon,
  Bot,
} from 'lucide-react'
import { Shell } from '../components/Shell'
import { CountdownClock } from '../components/CountdownClock'
import { CommitmentsPanel } from '../components/CommitmentsPanel'
import { PlanTimeline } from '../components/PlanTimeline'
import { AgentConsole } from '../components/AgentConsole'
import { CapacityPanel } from '../components/CapacityPanel'
import { CalibrationBadge } from '../components/CalibrationBadge'
import { Stat } from '../components/ui'
import { ClutchApi } from '../api'
import { formatMinutes } from '../lib/format'

function SectionHead({ icon, title, hint }: { icon: ReactNode; title: string; hint: string }) {
  return (
    <div className="mb-2 flex items-start gap-2.5">
      <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg border-2 border-line bg-surface-2 text-ember">
        {icon}
      </span>
      <div>
        <h2 className="font-display text-base font-700 leading-tight tracking-tight text-paper">{title}</h2>
        <p className="text-xs text-muted">{hint}</p>
      </div>
    </div>
  )
}

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
              Everything you owe, the time you actually have, and Clutch's call on what to do next.
            </p>
            <div className="mt-4 grid grid-cols-3 gap-3">
              <Stat value={active.length} label="to do" />
              <Stat value={plan.data?.schedule.length ?? 0} label="scheduled" />
              <Stat
                value={feasible ? <span className="inline-flex items-center gap-1"><CheckCircle2 className="h-5 w-5" />on track</span> : formatMinutes(deficit)}
                label={feasible ? 'status' : 'short by'}
                tone={feasible ? 'teal' : 'coral'}
              />
            </div>
            <div className="mt-3"><CalibrationBadge calibration={plan.data?.calibration} /></div>
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

      <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
        <div className="space-y-6 stagger">
          <div>
            <SectionHead icon={<ListChecks className="h-4 w-4" />} title="What you owe" hint="Every task with its deadline and how long it will really take. Add or edit tasks here." />
            <CommitmentsPanel />
          </div>
          <div>
            <SectionHead icon={<RouteIcon className="h-4 w-4" />} title="Clutch's plan" hint="The order to work in, honest time estimates, and whether you'll make every deadline." />
            <PlanTimeline />
          </div>
          <div>
            <SectionHead icon={<Bot className="h-4 w-4" />} title="Ask Clutch" hint="Ask what to drop or whether you'll make it — and get a plain-English answer." />
            <AgentConsole />
          </div>
        </div>
        <div className="stagger">
          <div className="lg:sticky lg:top-6">
            <SectionHead icon={<CalendarClock className="h-4 w-4" />} title="Your time" hint="The focus hours you really have before each deadline. Sync your calendar to block out busy time." />
            <CapacityPanel />
          </div>
        </div>
      </div>
    </Shell>
  )
}
