import { useEffect, useState } from 'react'
import { cx, formatCountdown, msUntil } from '../lib/format'

type Props = {
  /** ISO target instant. */
  target: string
  label?: string
  className?: string
}

/** Ticking monospace countdown to a deadline. Turns coral once overdue. */
export function CountdownClock({ target, label, className }: Props) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const remaining = msUntil(target, now)
  const overdue = remaining <= 0

  return (
    <div className={cx('flex flex-col', className)}>
      {label && <span className="stat-label">{label}</span>}
      <span
        className={cx(
          'font-mono text-3xl font-700 tabular-nums leading-none',
          overdue ? 'text-coral' : 'text-ember',
        )}
      >
        {overdue ? '-' : ''}
        {formatCountdown(remaining)}
      </span>
    </div>
  )
}
