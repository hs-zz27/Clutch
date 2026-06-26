import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { History, RotateCcw } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, Chip, EmptyState, ErrorNote, Panel, Spinner } from './ui'
import { cx, formatDateTime } from '../lib/format'

export function DecisionLedger() {
  const qc = useQueryClient()
  const ledger = useQuery({ queryKey: ['ledger'], queryFn: () => ClutchApi.listLedger(50) })

  const undo = useMutation({
    mutationFn: (id: number) => ClutchApi.undoLedger(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ledger'] })
      qc.invalidateQueries({ queryKey: ['commitments'] })
      qc.invalidateQueries({ queryKey: ['plan'] })
    },
  })

  return (
    <Panel title="Decision ledger" icon={<History className="h-4 w-4 text-ember" />} rail="amber">
      {ledger.isLoading ? (
        <div className="flex justify-center py-6"><Spinner /></div>
      ) : ledger.isError ? (
        <ErrorNote>Could not load the audit trail.</ErrorNote>
      ) : !ledger.data || ledger.data.length === 0 ? (
        <EmptyState icon={<History className="h-6 w-6" />} title="No actions yet" hint="Agent decisions and manual edits will appear here." />
      ) : (
        <ul className="space-y-2">
          {ledger.data.map((entry) => (
            <li key={entry.id} className={cx('rounded-lg border border-line-soft px-3 py-2', entry.undone ? 'bg-surface/50 opacity-60' : 'bg-surface-2')}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className={cx('truncate text-sm font-600', entry.undone && 'line-through')}>{entry.summary}</span>
                    {entry.undone && <Chip tone="muted">undone</Chip>}
                  </div>
                  <div className="mt-0.5 font-mono text-[10px] text-faint">
                    {formatDateTime(entry.created_at)} · {entry.action}
                  </div>
                  {entry.reasoning && (
                    <div className="mt-1.5 rounded bg-ink/50 px-2 py-1.5 text-xs text-muted">
                      <span className="font-600 uppercase tracking-wide text-ember">reason:</span> {entry.reasoning}
                    </div>
                  )}
                </div>
                {entry.reversible && !entry.undone && (
                  <Button variant="ghost" className="px-2 py-1 text-xs" loading={undo.isPending} onClick={() => undo.mutate(entry.id)}>
                    <RotateCcw className="mr-1.5 h-3.5 w-3.5" /> Undo
                  </Button>
                )}
              </div>
              {undo.isError && undo.variables === entry.id && (
                <div className="mt-2"><ErrorNote>{(undo.error as ApiError)?.detail ?? 'Failed to undo.'}</ErrorNote></div>
              )}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  )
}
