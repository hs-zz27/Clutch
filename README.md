<aside>
🚨

**Clutch** — the deadline-triage agent for when you've overcommitted and run out of time.

**It doesn't just list your tasks. It decides what to do fully, what to ship minimal, what to renegotiate, and what to drop — and tells you why.**

</aside>

## The problem

Every student and maker hits the same wall: five deadlines, one night, no plan. Todo apps happily show you all ten things you can't finish — they never tell you which three actually matter. Clutch is the *last-minute life saver*: give it your commitments and your real available time, and it triages like a calm senior who's been here before.

## How Clutch thinks

Clutch models your situation as **capacity vs. required effort**, then makes one decision per commitment using a value-density rule — *importance earned per remaining minute*.

| Decision | When Clutch picks it |
| --- | --- |
| **DO FULLY** | High value for the time it costs, and it fits the budget — protect it. |
| **SHIP MINIMAL** | Can't afford the full version, but a ~40% minimum-viable cut still lands. |
| **RENEGOTIATE** | No time left, but a known stakeholder can likely move the deadline. |
| **DROP** | Lowest value for its cost and no one to renegotiate with — cut it to save time. |

## Features

### 🧠 Capture & understand

- **Natural-language capture** — paste a messy brain-dump and Gemini turns it into structured commitments (title, deadline, effort, importance, stakeholder).
- **Image capture** — screenshot a syllabus, whiteboard, or chat and Clutch reads commitments straight off the picture (Gemini vision).
- **Dependencies & critical path** — link commitments with `depends_on`; Clutch validates the graph (no self-references, dangling links, or cycles) and plans along the critical path.
- **Decompose** — break a scary commitment into subtasks; Clutch clamps the estimates and defers the parent so effort is never double-counted (and it's reversible).

### ⚖️ Decide & plan

- **Triage engine** — ranks everything by value-density and assigns DO FULLY / SHIP MINIMAL / RENEGOTIATE / DROP against your real capacity.
- **Planner with p80 estimates** — schedules work using 80th-percentile effort (not optimistic guesses) and critical-path method so the timeline is honest.
- **Calibration that learns you** — Clutch compares your *actual* time against your estimates and learns a personal calibration factor (median ratio, clamped 0.25–4×, applied after 3+ samples). Plans, triage, and what-if all use the same factor, so the numbers always agree.
- **What-if sandbox** — simulate “what if I push this deadline / drop that / get 2 more hours?” and see baseline vs. scenario side by side before committing.

### 🤖 Act

- **AI agent** — give it a goal (“get me through tonight”) and a tool-using Gemini agent inspects your commitments, runs the planner and triage, and returns a final recommendation plus a full reasoning trace.
- **Renegotiation drafts** — Clutch writes the “can we move this?” message for you, with tone tuned to the relationship (a note to a professor reads differently than one to a teammate), then lets you edit and send.
- **Stakeholders directory** — track who each commitment is for, how formal to be, and notes that shape every renegotiation message.
- **Decision ledger + undo** — every action Clutch takes is recorded with its reasoning and is safely reversible; undo rolls back cleanly even if the world changed underneath it.

### 🔌 Connect

- **Calendar / capacity** — sync a calendar via ICS, track busy blocks, and compute your *real* focus capacity (work-day policy minus what's already booked).
- **Knowledge base (RAG)** — store reference documents and search them semantically so the agent can ground its answers.
- **Voice agent** — talk to Clutch hands-free through a LiveKit + Gemini Live native-audio session.

## Architecture

**Backend**

- FastAPI (async) + Uvicorn
- SQLAlchemy 2 async ORM
- PostgreSQL (Neon), Alembic migrations
- Google Gemini — text, vision, function-calling agent, and Live voice
- Python 3.12

**Frontend**

- React 19 + TypeScript
- Vite build, TanStack Query data layer
- Tailwind CSS 4 with a custom motion system
- War Room dashboard, plan timeline, commitments, renegotiation outbox

## API reference

| Area | Endpoints |
| --- | --- |
| Commitments | `GET/POST /commitments`, `PATCH/DELETE /commitments/{id}`, `POST /commitments/parse`, `POST /commitments/parse-image`, `POST /commitments/{id}/decompose` |
| Planning | `GET /plan`, `GET /calibration`, `POST /whatif` |
| Agent | `POST /agent` → `{ final_message, trace }` |
| Renegotiation | `POST /renegotiation/draft`, `PATCH /renegotiation/{id}`, `POST /renegotiation/{id}/send` |
| Stakeholders | `GET/POST /stakeholders`, `PATCH/DELETE /stakeholders/{id}` |
| Ledger | `GET /ledger`, `POST /ledger/{id}/undo` |
| Knowledge | `GET/POST /knowledge/documents`, `GET /knowledge/search` |
| Calendar | `GET /calendar/busy`, `POST /calendar/sync-ics`, `GET /calendar/capacity?until=` |
| Voice | `GET /voice/status`, `POST /voice/token` |
| System | `GET /healthz`, interactive docs at `/docs` |

## Data model

- **Commitment** — title, description, deadline, `est_effort_minutes`, `effort_p80_minutes`, `actual_minutes`, importance (1–5), stakeholder, minimum-viable definition, `depends_on_id` (self-reference), status (`not_started` / `in_progress` / `done` / `dropped` / `deferred`), progress %.
- **Stakeholder** — name, relationship, formality (1–5), notes.
- **Decision ledger** — action, target, summary, reasoning, payload, reversible / undone flags.
- Plus documents (knowledge base), renegotiation messages, and busy blocks (calendar).

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# configure environment
cp .env.example .env   # then fill in the values below

# run migrations
alembic upgrade head

# start the API
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive API, and `http://localhost:8000/healthz` to confirm it's alive.

**Core environment variables**

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Google Gemini key — powers parsing, vision, the agent, and voice. |
| `DATABASE_URL` | Async Postgres URL, e.g. Neon (`postgresql+asyncpg://…?ssl=require`). |
| `FRONTEND_ORIGIN` | Allowed CORS origin (default `http://localhost:5173`). |
| `TIMEZONE` | Planner clock (default `Asia/Calcutta`). |
| `WORK_DAY_START_HOUR` / `WORK_DAY_END_HOUR` | Daily focus window (default 9 → 23). |
| `MAX_FOCUS_HOURS_PER_DAY` | Cap on real focus time per day (default 10). |

<aside>
💡

Clutch is built to **degrade gracefully**: the app stays importable and bootable even when `DATABASE_URL` or `GEMINI_API_KEY` are unset, so smoke tests and CI never need live credentials. Real queries and AI calls still fail fast with a clear message if the values are missing.

</aside>

### Frontend

```bash
cd frontend
npm install
echo "VITE_CLUTCH_API_BASE=http://localhost:8000" > .env.local
npm run dev
```

### Optional integrations

- **Voice** — set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (plus `GEMINI_API_KEY`), install `requirements-voice.txt`, then run the voice agent. `GET /voice/status` reports whether it's enabled.
- **Email (renegotiation send)** — set `GMAIL_SENDER` and `GMAIL_APP_PASSWORD`.
- **Calendar** — set `CALENDAR_ICS_URL` to sync busy blocks for real capacity.

Every integration is optional — Clutch detects what's configured and quietly skips the rest.

## Reliability

- Deadlines are normalized to UTC at a single save chokepoint, so the planner never mixes naive and aware datetimes.
- Bulk capture (text & image) never persists an unvalidated dependency, so AI output can't trigger foreign-key 500s.
- The agent loop tolerates an empty model response and returns a clean partial result instead of crashing.
- A global error handler returns structured `500`s, and the decision ledger makes destructive actions reversible.

---

*Clutch — when the deadline's tonight, it tells you what actually matters.*