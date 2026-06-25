import { useQuery } from '@tanstack/react-query'
import { CalendarClock, TrendingDown } from 'lucide-react'
import { ClutchApi } from '../api'
import { Chip, EmptyState, ErrorNote, Panel, Skeleton } from './ui'
import { RISK_META } from '../lib/meta'
import { cx, formatDateTime, formatMinutes, relativeDeadline } from '../lib/format'

export function PlanTimeline() {
  const plan = useQuery({ queryKey: ['plan'], queryFn: ClutchApi.plan, refetchInterval: 30_000 })

  return (
    <Panel
      title="Plan timeline"
      icon={<CalendarClock className="h-4 w-4 text-ember" />}
      rail={plan.data && !plan.data.feasible ? 'coral' : 'teal'}
      actions={
        plan.data ? (
          <Chip tone={plan.data.feasible ? 'teal' : 'coral'}>
            {plan.data.feasible ? 'Feasible' : `Deficit ${formatMinutes(plan.data.total_deficit_minutes)}`}
          </Chip>
        ) : undefined
      }
    >
      {plan.isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : plan.isError ? (
        <ErrorNote>Could not compute the plan.</ErrorNote>
      ) : !plan.data || plan.data.schedule.length === 0 ? (
        <EmptyState icon={<CalendarClock className="h-6 w-6" />} title="No active work to schedule" hint="Add commitments that aren't done or dropped." />
      ) : (
        <>
          {!plan.data.feasible && (
            <div className="mb-3 flex items-start gap-2 rounded-lg border border-coral/40 bg-coral/10 px-3 py-2 text-sm text-coral">
              <TrendingDown className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                You are <b>{formatMinutes(plan.data.total_deficit_minutes)}</b> short of finishing everything on time. Run the agent to triage.
              </span>
            </div>
          )}
          <ol className="timeline stagger space-y-2">
            {plan.data.schedule.map((item) => {
              const rm = RISK_META[item.risk]
              return (
                <li key={item.id} className="relative pl-6">
                  <span className={cx(
                    'absolute left-0 top-2 h-3.5 w-3.5 rounded-full border-2 border-ink',
                    item.risk === 'on_track' && 'bg-teal',
                    item.risk === 'at_risk' && 'bg-amber',
                    item.risk === 'deficit' && 'bg-coral',
                  )} />
                  <div className="rounded-lg border border-line-soft bg-ink-2 px-3 py-2.5">
                    <div className="flex items-start justify-between gap-3">
                      <span className="truncate font-600">{item.title}</span>
                      <Chip tone={rm.tone}>{rm.label}</Chip>
                    </div>
                    <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 font-mono text-xs text-faint sm:grid-cols-4">
                      <span title="Remaining effort">{formatMinutes(item.remaining_minutes)} left</span>
                      <span title="Latest possible start">start by {formatDateTime(item.latest_start)}</span>
                      <span title="Deadline">{relativeDeadline(item.deadline)}</span>
                      {item.late_minutes > 0 ? (
                        <span className="text-coral">{formatMinutes(item.late_minutes)} late</span>
                      ) : (
                        <span className="text-teal">finishes {formatDateTime(item.projected_finish)}</span>
                      )}
                    </div>
                  </div>
                </li>
              )
            })}
          </ol>
        </>
      )}
    </Panel>
  )
}
