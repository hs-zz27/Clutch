import { useEffect, useState } from 'react'
import { cx, formatCountdown, msUntil } from '../lib/format'

type Props = {
  /** ISO target instant. */
  target: string
  label?: string
  className?: string
}

/** Ticking countdown. Ramps ember -> amber -> coral and pulses as the deadline closes. */
export function CountdownClock({ target, label, className }: Props) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const remaining = msUntil(target, now)
  const overdue = remaining <= 0
  const mins = remaining / 60000

  const tone: 'ember' | 'amber' | 'coral' =
    overdue || mins <= 60 ? 'coral' : mins <= 180 ? 'amber' : 'ember'
  const urgent = overdue || mins <= 60

  const color =
    tone === 'coral' ? 'text-coral' : tone === 'amber' ? 'text-amber' : 'text-ember'

  return (
    <div className={cx('flex flex-col', className)}>
      {label && <span className="stat-label">{label}</span>}
      <span
        className={cx(
          'font-mono text-3xl font-700 tabular-nums leading-none transition-colors duration-500',
          color,
          urgent && 'countdown-urgent',
        )}
      >
        {overdue ? '-' : ''}
        {formatCountdown(remaining)}
      </span>
    </div>
  )
}
