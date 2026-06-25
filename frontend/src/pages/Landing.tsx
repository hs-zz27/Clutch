import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Clock,
  Inbox,
  ListChecks,
  Radar,
  ShieldHalf,
  Sparkles,
} from 'lucide-react'
import { HealthBadge } from '../components/HealthBadge'
import { Chip } from '../components/ui'
import { cx } from '../lib/format'

const DECISIONS: Array<{
  key: string
  tone: 'teal' | 'amber' | 'iris' | 'coral'
  title: string
  blurb: string
}> = [
  { key: 'DO FULLY', tone: 'teal', title: 'Do fully', blurb: 'High stakes, time exists. Protect it and finish properly.' },
  { key: 'DO MINIMALLY', tone: 'amber', title: 'Do minimally', blurb: 'Ship the minimum viable version that still counts.' },
  { key: 'DEFER', tone: 'iris', title: 'Defer', blurb: 'Buy time — draft the renegotiation and push the date.' },
  { key: 'DROP', tone: 'coral', title: 'Drop', blurb: 'Low value, no room. Cut it loud so nothing rots silently.' },
]

const FLOW = [
  { icon: Inbox, label: 'Dump everything', text: 'Paste the chaos. Clutch parses commitments, deadlines and effort.' },
  { icon: Radar, label: 'Measure the gap', text: 'Real focus capacity vs. required minutes — the deficit, in the open.' },
  { icon: ShieldHalf, label: 'Triage', text: 'Every commitment gets a decision and a reason you can defend.' },
  { icon: ListChecks, label: 'Act', text: 'A timed plan plus drafted messages for whatever you push.' },
]

export default function Landing() {
  return (
    <div className="min-h-full">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-ember font-display text-lg font-700 text-ink">
            C
          </span>
          <span className="font-display text-base font-700 tracking-tight">Clutch</span>
        </div>
        <HealthBadge />
      </header>

      <section className="mx-auto grid max-w-6xl items-center gap-10 px-5 pb-10 pt-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="reveal">
          <div className="mb-5 flex items-center gap-2 font-mono text-xs uppercase tracking-[0.24em] text-faint">
            <Sparkles className="h-3.5 w-3.5 text-ember" />
            when everything is due at once
          </div>
          <h1 className="font-display text-5xl font-700 leading-[1.02] tracking-tight sm:text-6xl">
            Stop drowning.
            <br />
            <span className="text-ember-anim">Start triaging.</span>
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">
            Clutch is a deadline triage agent for the last-minute scramble. It weighs what
            you owe against the hours you actually have, then tells you what to finish, what
            to shrink, what to push, and what to cut — with the reasoning attached.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              to="/war-room"
              className="btn btn-ember text-base"
            >
              Open the War Room
              <ArrowRight className="h-4 w-4" />
            </Link>
            <span className="font-mono text-xs text-faint">no signup · single operator</span>
          </div>
          <div className="mt-10 grid grid-cols-2 gap-3 stagger sm:grid-cols-4">
            {FLOW.map((f, i) => (
              <div key={f.label} className="panel rail-ember p-4 hover-lift">
                <div className="flex items-center gap-2 text-faint">
                  <span className="font-mono text-xs">0{i + 1}</span>
                  <f.icon className="h-4 w-4 text-ember" />
                </div>
                <div className="mt-2 font-display text-sm font-700">{f.label}</div>
                <p className="mt-1 text-xs leading-snug text-muted">{f.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* sample triage card — product peek */}
        <div className="panel rail-coral reveal overflow-hidden">
          <div className="panel-head">
            <h3 className="panel-title">Triage · sample</h3>
            <Chip tone="coral">deficit 95m</Chip>
          </div>
          <div className="panel-body space-y-3 stagger">
            <div className="flex items-center justify-between font-mono text-xs text-faint">
              <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> capacity 240m</span>
              <span>required 335m</span>
            </div>
            {[
              { t: 'Ship investor update', d: 'DO FULLY', tone: 'teal' as const, m: '90m' },
              { t: 'Polish demo deck', d: 'DO MINIMALLY', tone: 'amber' as const, m: '40m' },
              { t: 'Reply to vendor RFP', d: 'DEFER', tone: 'iris' as const, m: '—' },
              { t: 'Reformat changelog', d: 'DROP', tone: 'coral' as const, m: '—' },
            ].map((r) => (
              <div key={r.t} className="flex items-center justify-between gap-3 rounded-lg border border-line-soft bg-ink-2 px-3 py-2.5">
                <span className="truncate text-sm">{r.t}</span>
                <span className="flex shrink-0 items-center gap-2">
                  <span className="font-mono text-xs text-faint">{r.m}</span>
                  <Chip tone={r.tone}>{r.d}</Chip>
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-16">
        <div className="mb-4 font-mono text-xs uppercase tracking-[0.24em] text-faint">
          four decisions, every time
        </div>
        <div className="grid gap-3 stagger sm:grid-cols-2 lg:grid-cols-4">
          {DECISIONS.map((d) => (
            <div key={d.key} className={cx('panel p-5 hover-lift', `rail-${d.tone}`)}>
              <Chip tone={d.tone}>{d.key}</Chip>
              <h4 className="mt-3 font-display text-lg font-700">{d.title}</h4>
              <p className="mt-1 text-sm leading-snug text-muted">{d.blurb}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="mx-auto max-w-6xl px-5 pb-10 text-xs text-faint">
        Clutch · deadline triage agent · built for the last-minute scramble.
      </footer>
    </div>
  )
}
