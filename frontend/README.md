# Clutch — Frontend

The **War Room** UI for Clutch, the deadline triage agent. When everything is due at
once, Clutch weighs what you owe against the focus time you actually have and tells you
what to **do fully**, **do minimally**, **defer**, or **drop** — with the reasoning
attached.

## Stack

- **React 19** + **TypeScript** + **Vite 8**
- **Tailwind CSS v4** (CSS-first `@theme` tokens, no config file)
- **TanStack Query** for server state, caching and polling
- **React Router 7** for the landing ↔ war-room split
- **lucide-react** icons

No state-management library and no UI kit — the design system lives in `src/index.css`
and a small primitive set in `src/components/ui.tsx`.

## Design language

A deliberately hand-built "operations desk" look: warm charcoal paper, a single ember
accent, hairline left-rails instead of heavy borders, and monospace numerals for every
timer, deadline and minute count. Decision colors are consistent everywhere — teal = do
fully / on track, amber = do minimally / at risk, iris = defer, coral = drop / deficit.

## Getting started

```bash
cd frontend
npm install
cp .env.example .env.local   # point VITE_CLUTCH_API_BASE at your backend
npm run dev                  # http://localhost:5173
```

The backend (FastAPI) should be running on the URL set in `VITE_CLUTCH_API_BASE`
(default `http://localhost:8000`).

## Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start the Vite dev server |
| `npm run build` | Type-check (`tsc -b`) and build for production |
| `npm run preview` | Preview the production build |
| `npm run lint` | Run ESLint |

## Structure

```
src/
  api.ts              Typed fetch client + ApiError (mirrors the FastAPI routes)
  types.ts            Domain models matching the backend schemas
  index.css           Tailwind v4 theme tokens + component classes
  lib/
    format.ts         Time / minute / countdown formatting helpers
    meta.ts           Status ↔ color/label maps (status, risk, decision, outbox)
  components/
    ui.tsx            Panel, Button, Chip, Stat, Modal, EmptyState…
    Shell.tsx         Sticky app frame (brand, live clock, health badge)
    CountdownClock.tsx
    HealthBadge.tsx
    CommitmentsPanel.tsx / CommitmentForm.tsx
    PlanTimeline.tsx
    CapacityPanel.tsx / CapacityMeter.tsx
    AgentConsole.tsx
    RenegotiationOutbox.tsx
    KnowledgePanel.tsx
  pages/
    Landing.tsx       Marketing entry screen
    WarRoom.tsx       The composed dashboard
```

## Features

- **Brain dump capture** — paste messy text, Gemini parses it into structured commitments.
- **Plan timeline** — risk-coded schedule with start-by times and a deficit banner.
- **Capacity & Clutch meter** — realistic focus minutes vs. required, plus busy blocks and optional ICS sync.
- **Triage agent** — one tap to run the agent and read its verdict + reasoning trace.
- **Renegotiation outbox** — AI-drafted deadline-extension emails you can edit and send.
- **Knowledge base** — upload documents and run grounded RAG queries.

Deployed as a static SPA (see `vercel.json` for rewrites).
