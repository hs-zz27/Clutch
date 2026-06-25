import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { useEffect } from 'react'
import { Loader2, X } from 'lucide-react'
import { cx } from '../lib/format'

export type Tone = 'ember' | 'teal' | 'amber' | 'coral' | 'iris' | 'muted'

/* Literal class maps so Tailwind v4 can statically detect every variant. */
export const CHIP_TONE: Record<Tone, string> = {
  ember: 'border-ember/40 text-ember',
  teal: 'border-teal/40 text-teal',
  amber: 'border-amber/40 text-amber',
  coral: 'border-coral/40 text-coral',
  iris: 'border-iris/40 text-iris',
  muted: 'border-line text-muted',
}

export const RAIL_TONE: Record<Tone, string> = {
  ember: 'rail-ember',
  teal: 'rail-teal',
  amber: 'rail-amber',
  coral: 'rail-coral',
  iris: 'rail-iris',
  muted: '',
}

export function Chip({ tone = 'muted', children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return <span className={cx('chip', CHIP_TONE[tone], className)}>{children}</span>
}

export function Panel({
  title,
  icon,
  actions,
  rail,
  bodyClassName,
  className,
  children,
}: {
  title?: ReactNode
  icon?: ReactNode
  actions?: ReactNode
  rail?: Tone
  bodyClassName?: string
  className?: string
  children: ReactNode
}) {
  return (
    <section className={cx('panel', rail && RAIL_TONE[rail], className)}>
      {(title || actions) && (
        <div className="panel-head">
          <div className="flex items-center gap-2">
            {icon}
            <h3 className="panel-title">{title}</h3>
          </div>
          {actions}
        </div>
      )}
      <div className={cx('panel-body', bodyClassName)}>{children}</div>
    </section>
  )
}

export function Stat({ value, label, tone }: { value: ReactNode; label: ReactNode; tone?: Tone }) {
  return (
    <div className={cx('stat', tone && RAIL_TONE[tone])}>
      <div className={cx('stat-num', tone === 'coral' && 'text-coral', tone === 'teal' && 'text-teal', tone === 'amber' && 'text-amber')}>
        {value}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'default' | 'ember' | 'ghost'
  loading?: boolean
}

export function Button({ variant = 'default', loading, disabled, children, className, ...rest }: ButtonProps) {
  return (
    <button
      className={cx('btn', variant === 'ember' && 'btn-ember', variant === 'ghost' && 'btn-ghost', className)}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  )
}

export function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label className="label" htmlFor={htmlFor}>
      {children}
    </label>
  )
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cx('h-4 w-4 animate-spin text-muted', className)} />
}

export function EmptyState({ icon, title, hint }: { icon?: ReactNode; title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-line py-10 text-center">
      {icon && <div className="text-faint">{icon}</div>}
      <p className="font-600 text-muted">{title}</p>
      {hint && <p className="max-w-sm text-sm text-faint">{hint}</p>}
    </div>
  )
}

export function ErrorNote({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-coral/40 bg-coral/10 px-3 py-2 text-sm text-coral">
      {children}
    </div>
  )
}

export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean
  onClose: () => void
  title: ReactNode
  children: ReactNode
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div
        className="panel mt-[6vh] w-full max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-head">
          <h3 className="panel-title">{title}</h3>
          <button className="btn-ghost btn px-2" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="panel-body">{children}</div>
      </div>
    </div>
  )
}
