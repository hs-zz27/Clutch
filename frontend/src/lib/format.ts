/** Tiny className combiner (keeps JSX readable without pulling in clsx). */
export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}

export function clamp(n: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, n))
}

/** 150 -> "2h 30m", 45 -> "45m", 0 -> "0m". Rounds to the nearest minute. */
export function formatMinutes(mins: number | null | undefined): string {
  if (mins == null || Number.isNaN(mins)) return '—'
  const total = Math.round(mins)
  if (total <= 0) return '0m'
  const h = Math.floor(total / 60)
  const m = total % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

/** Milliseconds until an ISO instant (negative if past). */
export function msUntil(iso: string, now: number = Date.now()): number {
  const t = new Date(iso).getTime()
  return Number.isNaN(t) ? 0 : t - now
}

/** Countdown string from ms: "03:12:45" or "12:45". Always non-negative. */
export function formatCountdown(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000))
  const hh = Math.floor(s / 3600)
  const mm = Math.floor((s % 3600) / 60)
  const ss = s % 60
  const pad = (n: number) => String(n).padStart(2, '0')
  return hh > 0 ? `${pad(hh)}:${pad(mm)}:${pad(ss)}` : `${pad(mm)}:${pad(ss)}`
}

/** Human relative deadline: "in 3h 12m" / "due now" / "5h 4m overdue". */
export function relativeDeadline(iso: string, now: number = Date.now()): string {
  const diff = msUntil(iso, now)
  const mins = Math.round(Math.abs(diff) / 60000)
  if (mins < 1) return 'due now'
  return diff >= 0 ? `in ${formatMinutes(mins)}` : `${formatMinutes(mins)} overdue`
}

const DATE_FMT = new Intl.DateTimeFormat(undefined, {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : DATE_FMT.format(d)
}

/** Convert a <input type="datetime-local"> value to an ISO string (local tz). */
export function localInputToIso(value: string): string {
  if (!value) return ''
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '' : d.toISOString()
}

/** Convert an ISO string to a <input type="datetime-local"> value. */
export function isoToLocalInput(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const off = d.getTimezoneOffset()
  const local = new Date(d.getTime() - off * 60000)
  return local.toISOString().slice(0, 16)
}

const MONTH_FMT = new Intl.DateTimeFormat(undefined, { month: 'short' })
const TIME_FMT = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' })

export function dayOfMonth(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : String(d.getDate())
}
export function monthShort(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '' : MONTH_FMT.format(d)
}
export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : TIME_FMT.format(d)
}
