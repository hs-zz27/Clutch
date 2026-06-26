import { useEffect, useMemo, useRef, useState } from 'react'
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react'
import { cx } from '../lib/format'

const WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

const pad = (n: number) => String(n).padStart(2, '0')

/** Parse a datetime-local value ("YYYY-MM-DDTHH:mm") into calendar parts. */
function parseValue(value: string): { date: Date | null; hour: number; minute: number } {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(value || '')
  if (m) {
    const date = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
    if (!Number.isNaN(date.getTime())) return { date, hour: Number(m[4]), minute: Number(m[5]) }
  }
  return { date: null, hour: 9, minute: 0 }
}

const toValue = (d: Date, h: number, mi: number) =>
  `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(h)}:${pad(mi)}`

/** 6×7 grid for the visible month, Monday-first (react-day-picker convention). */
function buildMonthGrid(year: number, month: number): Date[] {
  const first = new Date(year, month, 1)
  const offset = (first.getDay() + 6) % 7
  return Array.from({ length: 42 }, (_, i) => new Date(year, month, 1 - offset + i))
}

const sameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()

export function DateTimeField({
  value,
  onChange,
  placeholder = 'Select date & time',
  minuteStep = 5,
}: {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  minuteStep?: number
}) {
  const { date, hour, minute } = useMemo(() => parseValue(value), [value])
  const [open, setOpen] = useState(false)
  const today = useMemo(() => new Date(), [])
  const [view, setView] = useState(() => {
    const base = date ?? today
    return { year: base.getFullYear(), month: base.getMonth() }
  })
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (date) setView({ year: date.getFullYear(), month: date.getMonth() })
  }, [date])

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('mousedown', onDown)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('mousedown', onDown)
      window.removeEventListener('keydown', onKey)
    }
  }, [open])

  const grid = useMemo(() => buildMonthGrid(view.year, view.month), [view])

  const minutes = useMemo(() => {
    const base = Array.from({ length: Math.ceil(60 / minuteStep) }, (_, i) => i * minuteStep)
    if (!base.includes(minute)) base.push(minute)
    return base.sort((a, b) => a - b)
  }, [minute, minuteStep])

  const commit = (next: { date?: Date; hour?: number; minute?: number }) => {
    const d = next.date ?? date ?? today
    onChange(toValue(d, next.hour ?? hour, next.minute ?? minute))
  }

  const stepMonth = (delta: number) =>
    setView((v) => {
      const m = v.month + delta
      if (m < 0) return { year: v.year - 1, month: 11 }
      if (m > 11) return { year: v.year + 1, month: 0 }
      return { ...v, month: m }
    })

  const label = date
    ? new Intl.DateTimeFormat(undefined, {
        month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit',
      }).format(new Date(date.getFullYear(), date.getMonth(), date.getDate(), hour, minute))
    : ''

  return (
    <div className="dt" ref={ref}>
      <button
        type="button"
        className={cx('field dt-trigger', !date && 'dt-empty')}
        onClick={() => setOpen((v) => !v)}
      >
        <CalendarDays className="h-4 w-4 shrink-0 text-faint" />
        <span className="truncate">{date ? label : placeholder}</span>
      </button>

      {open && (
        <div className="dt-pop animate-scale-in">
          <div className="dt-cal-head">
            <button type="button" className="dt-nav" onClick={() => stepMonth(-1)} aria-label="Previous month">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="dt-month">{MONTHS[view.month]} {view.year}</span>
            <button type="button" className="dt-nav" onClick={() => stepMonth(1)} aria-label="Next month">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          <div className="dt-grid dt-weekdays">
            {WEEKDAYS.map((w) => <span key={w} className="dt-weekday">{w}</span>)}
          </div>
          <div className="dt-grid">
            {grid.map((d) => (
              <button
                key={d.toISOString()}
                type="button"
                className={cx(
                  'dt-day',
                  d.getMonth() !== view.month && 'dt-day-muted',
                  sameDay(d, today) && 'dt-day-today',
                  date && sameDay(d, date) && 'dt-day-sel',
                )}
                onClick={() => commit({ date: d })}
              >
                {d.getDate()}
              </button>
            ))}
          </div>

          <div className="dt-time">
            <span className="dt-time-label">Time</span>
            <div className="dt-time-selects">
              <select className="dt-select" value={hour} onChange={(e) => commit({ hour: Number(e.target.value) })}>
                {Array.from({ length: 24 }, (_, h) => <option key={h} value={h}>{pad(h)}</option>)}
              </select>
              <span className="dt-colon">:</span>
              <select className="dt-select" value={minute} onChange={(e) => commit({ minute: Number(e.target.value) })}>
                {minutes.map((m) => <option key={m} value={m}>{pad(m)}</option>)}
              </select>
            </div>
            <button
              type="button"
              className="dt-now"
              onClick={() => {
                const n = new Date()
                commit({ date: n, hour: n.getHours(), minute: n.getMinutes() - (n.getMinutes() % minuteStep) })
              }}
            >
              Now
            </button>
          </div>

          <div className="dt-foot">
            <button type="button" className="dt-done" onClick={() => setOpen(false)}>Done</button>
          </div>
        </div>
      )}
    </div>
  )
}
