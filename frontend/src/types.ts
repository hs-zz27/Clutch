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
  importance: number
  stakeholder: string | null
  min_viable_definition: string | null
  status: CommitmentStatus
  progress_pct: number
  created_at: string
}

export interface CommitmentCreate {
  title: string
  description?: string | null
  deadline: string
  est_effort_minutes?: number
  importance?: number
  stakeholder?: string | null
  min_viable_definition?: string | null
}

export interface CommitmentUpdate {
  title?: string
  description?: string | null
  deadline?: string
  est_effort_minutes?: number
  importance?: number
  stakeholder?: string | null
  min_viable_definition?: string | null
  status?: CommitmentStatus
  progress_pct?: number
}

export type PlanRisk = 'on_track' | 'at_risk' | 'deficit'

export interface PlanItem {
  id: number
  title: string
  importance: number
  deadline: string
  remaining_minutes: number
  projected_finish: string
  latest_start: string
  late_minutes: number
  risk: PlanRisk
}

export interface Plan {
  now: string
  schedule: PlanItem[]
  total_deficit_minutes: number
  feasible: boolean
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

/* Triage decisions are produced by the backend run_triage tool and surfaced
 * inside the agent trace. Typed here so the War Room can render them richly. */
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
