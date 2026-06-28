import type {
  AgentResponse,
  BusyBlock,
  BusyBlockCreate,
  Calibration,
  Capacity,
  Commitment,
  CommitmentCreate,
  CommitmentUpdate,
  DecomposeResult,
  Health,
  KnowledgeDocument,
  KnowledgeSearchResponse,
  LedgerPage,
  Plan,
  RenegotiationGenerateRequest,
  RenegotiationMessage,
  RenegotiationUpdate,
  Stakeholder,
  StakeholderCreate,
  StakeholderUpdate,
  WhatIfResult,
  WhatIfScenario,
} from './types'

const BASE = import.meta.env.VITE_CLUTCH_API_BASE ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  detail: string
  body?: unknown

  constructor(status: number, detail: string, body?: unknown) {
    super(`[${status}] ${detail}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.body = body
  }
}

type Opts = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  query?: Record<string, string | number | undefined>
  timeoutMs?: number
}

export async function api<T>(path: string, opts: Opts = {}): Promise<T> {
  const { method = 'GET', body, query, timeoutMs = 60000 } = opts

  const url = new URL(BASE + path)
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v))
    }
  }

  const isForm = typeof FormData !== 'undefined' && body instanceof FormData
  const headers: Record<string, string> = {}
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json'

  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)
  let res: Response
  try {
    res = await fetch(url, {
      method,
      headers,
      body:
        body === undefined
          ? undefined
          : isForm
            ? (body as FormData)
            : JSON.stringify(body),
      signal: ctrl.signal,
    })
    } catch (e) {
      const aborted =
        ctrl.signal.aborted ||
        (e instanceof DOMException && e.name === 'AbortError')
      if (aborted) {
        throw new ApiError(
          0,
          'The request timed out. If you were uploading a file, it may be too large or your connection is slow.',
        )
      }
      throw new ApiError(0, e instanceof Error ? e.message : 'network error')
    } finally {
    clearTimeout(timer)
  }

  if (res.status === 204) return undefined as T

  const text = await res.text()
  let parsed: unknown = undefined
  if (text) {
    try {
      parsed = JSON.parse(text)
    } catch {
      parsed = text
    }
  }

  if (!res.ok) {
    const detail =
      parsed && typeof parsed === 'object' && 'detail' in parsed
        ? String((parsed as { detail: unknown }).detail)
        : res.statusText || 'request failed'
    throw new ApiError(res.status, detail, parsed)
  }
  return parsed as T
}

export type VoiceStatus = {
  enabled: boolean
  model: string
  voice: string
  room: string
}

export type VoiceToken = {
  url: string
  token: string
  room: string
  identity: string
}

export const ClutchApi = {
  health: () => api<Health>('/healthz'),

  // Commitments
  listCommitments: () => api<Commitment[]>('/commitments'),
  createCommitment: (payload: CommitmentCreate) =>
    api<Commitment>('/commitments', { method: 'POST', body: payload }),
  updateCommitment: (id: number, payload: CommitmentUpdate) =>
    api<Commitment>(`/commitments/${id}`, { method: 'PATCH', body: payload }),
  deleteCommitment: (id: number) =>
    api<void>(`/commitments/${id}`, { method: 'DELETE' }),
  parseCommitments: (text: string) =>
    api<Commitment[]>('/commitments/parse', { method: 'POST', body: { text } }),
  parseImage: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api<Commitment[]>('/commitments/parse-image', { method: 'POST', body: fd })
  },
  decompose: (id: number, persist = true) =>
    api<DecomposeResult>(`/commitments/${id}/decompose`, { method: 'POST', body: { persist } }),

  // Planner
  plan: () => api<Plan>('/plan'),

  // Calibration
  getCalibration: () => api<Calibration>('/calibration'),

  // Decision ledger
  listLedger: (limit = 20, offset = 0) =>
    api<LedgerPage>('/ledger', { query: { limit, offset } }),
  undoLedger: (id: number) => api<{ ok: boolean }>(`/ledger/${id}/undo`, { method: 'POST' }),

  // Stakeholders
  listStakeholders: () => api<Stakeholder[]>('/stakeholders'),
  createStakeholder: (body: StakeholderCreate) =>
    api<Stakeholder>('/stakeholders', { method: 'POST', body }),
  updateStakeholder: (id: number, body: StakeholderUpdate) =>
    api<Stakeholder>(`/stakeholders/${id}`, { method: 'PATCH', body }),
  deleteStakeholder: (id: number) =>
    api<void>(`/stakeholders/${id}`, { method: 'DELETE' }),

  // What-if simulator
  runWhatIf: (scenario: WhatIfScenario) =>
    api<WhatIfResult>('/whatif', { method: 'POST', body: scenario }),

  // Agent
  runAgent: (goal: string) =>
    api<AgentResponse>('/agent', { method: 'POST', body: { goal } }),

  // Knowledge / RAG
  listDocuments: () => api<KnowledgeDocument[]>('/knowledge/documents'),
  uploadDocument: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api<KnowledgeDocument>('/knowledge/documents', { method: 'POST', body: fd })
  },
  searchKnowledge: (query: string) =>
    api<KnowledgeSearchResponse>('/knowledge/search', { method: 'POST', body: { query } }),
  deleteDocument: (id: number) =>
    api<void>(`/knowledge/documents/${id}`, { method: 'DELETE' }),

  // Renegotiation outbox
  listRenegotiations: () => api<RenegotiationMessage[]>('/renegotiation'),
  draftRenegotiation: (payload: RenegotiationGenerateRequest) =>
    api<RenegotiationMessage>('/renegotiation/draft', { method: 'POST', body: payload }),
  editRenegotiation: (id: number, payload: RenegotiationUpdate) =>
    api<RenegotiationMessage>(`/renegotiation/${id}`, { method: 'PATCH', body: payload }),
  sendRenegotiation: (id: number) =>
    api<RenegotiationMessage>(`/renegotiation/${id}/send`, { method: 'POST' }),

  // Calendar / capacity
  listBusyBlocks: () => api<BusyBlock[]>('/calendar/busy'),
  createBusyBlock: (payload: BusyBlockCreate) =>
    api<BusyBlock>('/calendar/busy', { method: 'POST', body: payload }),
  deleteBusyBlock: (id: number) =>
    api<void>(`/calendar/busy/${id}`, { method: 'DELETE' }),
  syncIcs: () => api<Record<string, unknown>>('/calendar/sync-ics', { method: 'POST' }),
  capacity: (until?: string) =>
    api<Capacity>('/calendar/capacity', { query: { until } }),

  // Voice Crisis Mode
  voiceStatus: () => api<VoiceStatus>('/voice/status'),
  voiceToken: (body: { room?: string; identity?: string } = {}) =>
    api<VoiceToken>('/voice/token', { method: 'POST', body }),
}
