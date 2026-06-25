import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Bot, ChevronDown, Play, Terminal } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, ErrorNote, Panel } from './ui'
import { cx } from '../lib/format'
import type { AgentResponse, AgentTraceStep } from '../types'

const DEFAULT_GOAL = "I'm running out of time. Tell me what to do."

function prettyValue(v: unknown): string {
  if (v == null) return ''
  if (typeof v === 'string') return v
  return JSON.stringify(v, null, 2)
}

function TraceCard({ step, index }: { step: AgentTraceStep; index: number }) {
  const [open, setOpen] = useState(false)
  const tool = (step.tool ?? step.action ?? step.name ?? step.type ?? `step ${index + 1}`) as string
  const thought = (step.thought ?? step.reasoning ?? step.message) as string | undefined
  const observation = step.observation ?? step.result ?? step.output

  return (
    <div className="rounded-lg border border-line-soft bg-ink-2">
      <button className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left" onClick={() => setOpen((v) => !v)}>
        <span className="flex items-center gap-2 font-mono text-xs">
          <span className="text-faint">{String(index + 1).padStart(2, '0')}</span>
          <span className="text-ember">{tool}</span>
        </span>
        <ChevronDown className={cx('h-4 w-4 text-faint transition-transform', open && 'rotate-180')} />
      </button>
      {open && (
        <div className="space-y-2 border-t border-line-soft px-3 py-2 text-sm">
          {thought && <p className="text-muted">{thought}</p>}
          {step.tool_input != null && (
            <pre className="overflow-x-auto rounded bg-ink p-2 font-mono text-xs text-faint">{prettyValue(step.tool_input)}</pre>
          )}
          {observation != null && (
            <pre className="overflow-x-auto rounded bg-ink p-2 font-mono text-xs text-paper/80">{prettyValue(observation)}</pre>
          )}
        </div>
      )}
    </div>
  )
}

export function AgentConsole() {
  const qc = useQueryClient()
  const [goal, setGoal] = useState(DEFAULT_GOAL)
  const [result, setResult] = useState<AgentResponse | null>(null)

  const run = useMutation({
    mutationFn: () => ClutchApi.runAgent(goal.trim() || DEFAULT_GOAL),
    onSuccess: (res) => {
      setResult(res)
      qc.invalidateQueries({ queryKey: ['plan'] })
      qc.invalidateQueries({ queryKey: ['renegotiations'] })
    },
  })

  return (
    <Panel
      title="Triage agent"
      icon={<Bot className="h-4 w-4 text-ember" />}
      rail="iris"
      actions={
        <Button variant="ember" loading={run.isPending} onClick={() => run.mutate()}>
          <Play className="h-4 w-4" /> Run triage
        </Button>
      }
    >
      <textarea
        className="field min-h-[56px] resize-y"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder={DEFAULT_GOAL}
      />
      <p className="mt-2 font-mono text-xs text-faint">
        The agent reads your commitments + capacity, decides do / minimize / defer / drop, and rewrites the plan.
      </p>

      {run.isError && <div className="mt-3"><ErrorNote>{(run.error as ApiError)?.detail ?? 'Agent run failed.'}</ErrorNote></div>}

      {result && (
        <div className="mt-4 space-y-3">
          <div className="rounded-lg border border-ember/40 bg-ember/10 px-3 py-3">
            <div className="mb-1 flex items-center gap-1.5 font-mono text-xs uppercase tracking-wide text-ember">
              <Terminal className="h-3.5 w-3.5" /> verdict
            </div>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-paper">{result.final_message}</p>
          </div>
          {result.trace?.length > 0 && (
            <div>
              <div className="mb-1.5 font-mono text-xs uppercase tracking-wide text-faint">reasoning trace</div>
              <div className="space-y-1.5">
                {result.trace.map((s, i) => <TraceCard key={i} step={s} index={i} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </Panel>
  )
}
