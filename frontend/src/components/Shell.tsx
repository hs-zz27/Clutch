import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Mic } from 'lucide-react'
import { HealthBadge } from './HealthBadge'

function LiveClock() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return (
    <span className="font-mono text-sm tabular-nums text-muted">
      {now.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
    </span>
  )
}

/** Sticky app frame: brand mark + crisis entry + live clock + health badge. */
export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-30 border-b border-line bg-ink/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-ember font-display text-lg font-700 text-ink">
              C
            </span>
            <span className="flex flex-col leading-none">
              <span className="font-display text-base font-700 tracking-tight text-paper">
                Clutch
              </span>
              <span className="text-[10px] font-600 uppercase tracking-[0.22em] text-faint">
                deadline triage
              </span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/crisis" className="btn btn-ember px-3 py-1.5 text-sm">
              <Mic className="h-4 w-4" />
              <span className="hidden sm:inline">Crisis Mode</span>
            </Link>
            <LiveClock />
            <HealthBadge />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-5 py-6">{children}</main>
      <footer className="mx-auto max-w-7xl px-5 pb-8 pt-2 text-xs text-faint">
        Clutch · last-minute triage for when everything is due at once.
      </footer>
    </div>
  )
}
