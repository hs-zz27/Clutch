import { useQuery } from '@tanstack/react-query'
import { CalendarClock, GitBranch, TrendingDown } from 'lucide-react'
import { ClutchApi } from '../api'
import { CalibrationBadge } from './CalibrationBadge'
import { Chip, EmptyState, ErrorNote, Panel, Skeleton } from './ui'
import { RISK_META } from '../lib/meta'
import { cx, formatDateTime, formatMinutes, relativeDeadline } from '../lib/format'
import type { MakeProbability } from '../types'

const PROB_TONE: Record<MakeProbability, 'teal' | 'amber' | 'coral'> = {
  high: 'teal',
  medium: 'amber',
  low: 'coral',
}

export function PlanTimeline() {
  const plan = useQuery({ queryKey: ['plan'], queryFn: ClutchApi.plan, refetchInterval: 30_000 })
  const data = plan.data
  const prob = data?.make_probability

  return (
    <Panel
      title="Plan timeline"
      icon={<CalendarClock className="h-4 w-4 text-ember" />}
      rail={data && !data.feasible ? 'coral' : 'teal'}
      actions={
        data ? (
          <span className="flex items-center gap-1.5">
            <CalibrationBadge calibration={data.calibration} />
            {prob && <Chip tone={PROB_TONE[prob]}>{prob} odds</Chip>}
            <Chip tone={data.feasible ? 'teal' : 'coral'}>
              {data.feasible ? 'Feasible' : `Deficit ${formatMinutes(data.total_deficit_minutes)}`}
            </Chip>
          </span>
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
      ) : !data || data.schedule.length === 0 ? (
        <EmptyState icon={<CalendarClock className="h-6 w-6" />} title="No active work to schedule" hint="Add commitments that aren't done or dropped." />
      ) : (
        <>
          {!data.feasible && (
            <div className="mb-3 flex items-start gap-2 rounded-lg border-2 border-coral bg-coral/10 px-3 py-2 text-sm text-coral">
              <TrendingDown className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                You are <b>{formatMinutes(data.total_deficit_minutes)}</b> short on the likely plan
                {data.total_deficit_minutes_p80 != null && data.total_deficit_minutes_p80 > data.total_deficit_minutes && (
                  <> — up to <b>{formatMinutes(data.total_deficit_minutes_p80)}</b> in the worst case</>
                )}
                . Run the agent to triage.
              </span>
            </div>
          )}
          <ol className="timeline stagger space-y-2">
            {data.schedule.map((item) => {
              const rm = RISK_META[item.risk]
              const p80 = item.remaining_minutes_p80
              const lateP80 = item.late_minutes_p80
              return (
                <li key={item.id} className="relative pl-6">
                  <span className={cx(
                    'absolute left-0 top-2 h-3.5 w-3.5 rounded-full border-2 border-surface',
                    item.risk === 'on_track' && 'bg-teal',
                    item.risk === 'at_risk' && 'bg-amber',
                    item.risk === 'deficit' && 'bg-coral',
                  )} />
                  <div className="rounded-lg border border-line-soft bg-ink-2 px-3 py-2.5">
                    <div className="flex items-start justify-between gap-3">
                      <span className="flex min-w-0 items-center gap-1.5 font-600">
                        {item.depends_on_id != null && <GitBranch className="h-3.5 w-3.5 shrink-0 text-iris" />}
                        <span className="truncate">{item.title}</span>
                      </span>
                      <Chip tone={rm.tone}>{rm.label}</Chip>
                    </div>
                    <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 font-mono text-xs text-faint sm:grid-cols-4">
                      <span title="Remaining effort (likely · worst case)">
                        {formatMinutes(item.remaining_minutes)} left
                        {p80 != null && p80 > item.remaining_minutes && <span className="text-amber"> · {formatMinutes(p80)} p80</span>}
                      </span>
                      <span title="Latest possible start">start by {formatDateTime(item.latest_start)}</span>
                      <span title="Deadline">{relativeDeadline(item.deadline)}</span>
                      {item.late_minutes > 0 ? (
                        <span className="text-coral">
                          {formatMinutes(item.late_minutes)} late
                          {lateP80 != null && lateP80 > item.late_minutes && <span> · {formatMinutes(lateP80)} p80</span>}
                        </span>
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
