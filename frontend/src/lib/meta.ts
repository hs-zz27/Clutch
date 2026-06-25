import type { CommitmentStatus, OutboxStatus, PlanRisk, TriageDecision } from '../types'
import type { Tone } from '../components/ui'

export const STATUS_META: Record<CommitmentStatus, { label: string; tone: Tone }> = {
  not_started: { label: 'Not started', tone: 'muted' },
  in_progress: { label: 'In progress', tone: 'ember' },
  done: { label: 'Done', tone: 'teal' },
  dropped: { label: 'Dropped', tone: 'coral' },
  deferred: { label: 'Deferred', tone: 'iris' },
}

export const RISK_META: Record<PlanRisk, { label: string; tone: Tone }> = {
  on_track: { label: 'On track', tone: 'teal' },
  at_risk: { label: 'At risk', tone: 'amber' },
  deficit: { label: 'Deficit', tone: 'coral' },
}

export const DECISION_META: Record<TriageDecision, { label: string; tone: Tone }> = {
  DO_FULLY: { label: 'Do fully', tone: 'teal' },
  DO_MINIMALLY: { label: 'Do minimally', tone: 'amber' },
  DEFER: { label: 'Defer', tone: 'iris' },
  DROP: { label: 'Drop', tone: 'coral' },
}

export const OUTBOX_META: Record<OutboxStatus, { label: string; tone: Tone }> = {
  draft: { label: 'Draft', tone: 'muted' },
  approved: { label: 'Approved', tone: 'iris' },
  sent: { label: 'Sent', tone: 'teal' },
  failed: { label: 'Failed', tone: 'coral' },
}

export const IMPORTANCE_LABEL: Record<number, string> = {
  1: 'Trivial',
  2: 'Low',
  3: 'Normal',
  4: 'High',
  5: 'Critical',
}
