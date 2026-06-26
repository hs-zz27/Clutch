import { useState } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, History, RotateCcw } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, Chip, EmptyState, ErrorNote, Panel, Spinner } from './ui'
import { cx, formatDateTime } from '../lib/format'

const PAGE_SIZE = 10

export function DecisionLedger() {
  const qc = useQueryClient()
  const [page, setPage] = useState(0)
  const ledger = useQuery({
    queryKey: ['ledger', page],
    queryFn: () => ClutchApi.listLedger(PAGE_SIZE, page * PAGE_SIZE),
    placeholderData: keepPreviousData,
  })

  const undo = useMutation({
    mutationFn: (id: number) => ClutchApi.undoLedger(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ledger'] })
      qc.invalidateQueries({ queryKey: ['commitments'] })
      qc.invalidateQueries({ queryKey: ['plan'] })
    },
  })

  const total = ledger.data?.total ?? 0
  const entries = ledger.data?.items ?? []
  const start = total === 0 ? 0 : page * PAGE_SIZE + 1
  const end = Math.min(total, page * PAGE_SIZE + entries.length)
  const hasPrev = page > 0
  const hasNext = (page + 1) * PAGE_SIZE < total

  return (
    <Panel
      title="Decision ledger"
      icon={<History className="h-4 w-4 text-ember" />}
      rail="amber"
      actions={
        total > 0 ? (
          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] text-faint">{start}–{end} of {total}</span>
            <Button variant="ghost" className="px-2 py-1" disabled={!hasPrev || ledger.isFetching} onClick={() => setPage((p) => Math.max(0, p - 1))}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="ghost" className="px-2 py-1" disabled={!hasNext || ledger.isFetching} onClick={() => setPage((p) => p + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        ) : undefined
      }
    >
      {ledger.isLoading ? (
        <div className="flex justify-center py-6"><Spinner /></div>
      ) : ledger.isError ? (
        <ErrorNote>Could not load the audit trail.</ErrorNote>
      ) : entries.length === 0 ? (
        <EmptyState icon={<History className="h-6 w-6" />} title="No actions yet" hint="Agent decisions and manual edits will appear here." />
      ) : (
        <ul className={cx('space-y-2 transition-opacity', ledger.isFetching && 'opacity-60')}>
          {entries.map((entry) => (
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
