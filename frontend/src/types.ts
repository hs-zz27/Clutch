/*
 * Mirrors the Clutch FastAPI schemas. ISO-8601 datetimes are carried as strings.
 */

export type CommitmentStatus =
  | 'not_started'
  | 'in_progress'
  | 'done'
  | 'dropped'
  | 'deferred'

export interface Commitment {
  id: number
  title: string
  description: string | null
  deadline: string
  est_effort_minutes: number
  effort_p80_minutes?: number | null
  actual_minutes?: number | null
  importance: number
  stakeholder: string | null
  min_viable_definition: string | null
  depends_on_id?: number | null
  status: CommitmentStatus
  progress_pct: number
  created_at: string
}

export interface CommitmentCreate {
  title: string
  description?: string | null
  deadline: string
  est_effort_minutes?: number
  effort_p80_minutes?: number | null
  importance?: number
  stakeholder?: string | null
  min_viable_definition?: string | null
  depends_on_id?: number | null
}

export interface CommitmentUpdate {
  title?: string
  description?: string | null
  deadline?: string
  est_effort_minutes?: number
  effort_p80_minutes?: number | null
  actual_minutes?: number | null
  importance?: number
  stakeholder?: string | null
  min_viable_definition?: string | null
  depends_on_id?: number | null
  status?: CommitmentStatus
  progress_pct?: number
}

export type PlanRisk = 'on_track' | 'at_risk' | 'deficit'
export type MakeProbability = 'high' | 'medium' | 'low'

export interface PlanItem {
  id: number
  title: string
  importance: number
  deadline: string
  depends_on_id?: number | null
  remaining_minutes: number
  remaining_minutes_p80?: number
  projected_finish: string
  projected_finish_p80?: string
  latest_start: string
  late_minutes: number
  late_minutes_p80?: number
  risk: PlanRisk
}

export interface Plan {
  now: string
  schedule: PlanItem[]
  total_deficit_minutes: number
  total_deficit_minutes_p80?: number
  feasible: boolean
  feasible_worst_case?: boolean
  calibration_factor?: number
  make_probability?: MakeProbability
  calibration?: Calibration
}

export interface Calibration {
  factor: number
  sample_size: number
  applied: boolean
  effective_factor: number
  tendency: string
}

export interface LedgerEntry {
  id: number
  action: string
  target_type: string
  target_id: number | null
  summary: string
  reasoning: string | null
  payload: Record<string, unknown> | null
  reversible: boolean
  undone: boolean
  created_at: string
}

export interface LedgerPage {
  items: LedgerEntry[]
  total: number
  limit: number
  offset: number
}

export interface Stakeholder {
  id: number
  name: string
  relationship: string | null
  formality: number
  notes: string | null
  created_at: string
}

export interface StakeholderCreate {
  name: string
  relationship?: string | null
  formality?: number
  notes?: string | null
}

export type StakeholderUpdate = Partial<StakeholderCreate>

export interface SubtaskSuggestion {
  title: string
  est_effort_minutes: number
  effort_p80_minutes: number | null
}

export interface DecomposeResult {
  commitment_id: number
  persisted: boolean
  parent_deferred: boolean
  subtasks: SubtaskSuggestion[]
  created_ids: number[]
}

export interface WhatIfAddCommitment {
  title: string
  deadline: string
  est_effort_minutes: number
  effort_p80_minutes?: number | null
  importance?: number
  stakeholder?: string | null
  depends_on_id?: number | null
}

export interface WhatIfScenario {
  drop_ids?: number[]
  complete_ids?: number[]
  deadline_overrides?: Record<number, string>
  effort_overrides?: Record<number, { est_effort_minutes?: number; effort_p80_minutes?: number }>
  extra_focus_minutes?: number
  add_commitments?: WhatIfAddCommitment[]
}

export interface WhatIfDiff {
  deficit_minutes_before: number
  deficit_minutes_after: number
  deficit_minutes_delta: number
  feasible_before: boolean
  feasible_after: boolean
  make_probability_before: string
  make_probability_after: string
  worst_case_deficit_before: number
  worst_case_deficit_after: number
}

export interface WhatIfResult {
  now: string
  calibration_factor: number
  baseline: { plan: Plan; triage?: unknown }
  scenario: { plan: Plan; triage?: unknown }
  diff: WhatIfDiff
}

/** A single step in the agent's ReAct trace. Shape is intentionally loose. */
export type AgentTraceStep = Record<string, any>

export interface AgentResponse {
  final_message: string
  trace: AgentTraceStep[]
}

export interface KnowledgeDocument {
  id: number
  filename: string
  content_type: string | null
  size_bytes: number | null
  uploaded_at: string
}

export interface KnowledgeSearchResponse {
  answer: string
  citations: string[]
}

export type OutboxStatus = 'draft' | 'approved' | 'sent' | 'failed'

export interface RenegotiationMessage {
  id: number
  commitment_id: number
  recipient: string | null
  subject: string
  body: string
  status: OutboxStatus
  error: string | null
  created_at: string
  sent_at: string | null
}

export interface RenegotiationGenerateRequest {
  commitment_id: number
  tone?: string
}

export interface RenegotiationUpdate {
  recipient?: string | null
  subject?: string | null
  body?: string | null
}

export interface BusyBlock {
  id: number
  start: string
  end: string
  label: string | null
  source: string
  external_uid: string | null
  created_at: string
}

export interface BusyBlockCreate {
  start: string
  end: string
  label?: string | null
}

export interface Capacity {
  from_time: string
  until: string
  available_minutes: number
  available_hours: number
}

export interface Health {
  status: string
}

export type TriageDecision = 'DO_FULLY' | 'DO_MINIMALLY' | 'DEFER' | 'DROP'

export interface TriageItem {
  id: number
  title: string
  importance: number
  remaining_minutes: number
  stakeholder: string | null
  decision: TriageDecision
  reason: string
  salvage_minutes: number | null
}

export interface TriageResult {
  feasible: boolean
  capacity_minutes: number
  required_minutes: number
  deficit_minutes: number
  decisions: TriageItem[]
  plan: Plan
}
