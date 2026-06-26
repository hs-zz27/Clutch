import { cx, formatMinutes } from '../lib/format'

/** The signature gauge: realistic focus minutes available vs. minutes required. */
export function CapacityMeter({ available, required }: { available: number; required: number }) {
  const max = Math.max(available, required, 1)
  const availPct = (available / max) * 100
  const reqPct = (required / max) * 100
  const deficit = Math.max(0, required - available)
  const tone = deficit > 0 ? 'coral' : 'teal'

  return (
    <div>
      <div className="flex items-end justify-between">
        <div>
          <div className="stat-label">Clutch meter</div>
          <div className={cx('font-mono text-2xl font-700 tabular-nums', tone === 'coral' ? 'text-coral' : 'text-teal')}>
            {deficit > 0 ? `−${formatMinutes(deficit)}` : 'Clear'}
          </div>
        </div>
        <div className="text-right font-mono text-xs text-faint">
          <div>{formatMinutes(available)} available</div>
          <div>{formatMinutes(required)} required</div>
        </div>
      </div>
      <div className="relative mt-3 h-4 overflow-hidden rounded-full border-2 border-line bg-surface">
        <div className="absolute inset-y-0 left-0 bg-teal" style={{ width: `${availPct}%` }} />
        <div
          className={cx('absolute inset-y-0', deficit > 0 ? 'bg-coral' : 'bg-transparent')}
          style={{ left: `${availPct}%`, width: `${Math.max(0, reqPct - availPct)}%` }}
        />
      </div>
      <div className="mt-1.5 flex items-center gap-4 font-mono text-[10px] uppercase tracking-wide text-faint">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm border border-line bg-teal" /> capacity</span>
        {deficit > 0 && <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm border border-line bg-coral" /> shortfall</span>}
      </div>
    </div>
  )
}
