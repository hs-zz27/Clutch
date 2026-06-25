# Clutch - Voice Crisis Mode (Phase 8)

Hands-free crisis triage. Tap the mic in the web app and say _"Clutch, what do I
do right now?"_ - the agent speaks back through a **Gemini Live** native-audio
model and runs the **same** plan/triage/renegotiation logic as the typed agent.

## How it fits together

```
Browser (Crisis Mode UI)
   |  1. POST /voice/token   ->  Clutch API mints a short-lived, room-scoped token
   |  2. join room (WebRTC)  ->  LiveKit Cloud
                                     ^
                                     |  auto-joins the room
                           Voice worker (this package)
                                     |  Gemini Live (audio in/out) + Silero VAD
                                     |  function tools call ...
                                     v
                           Clutch API  (/agent, /commitments, /plan,
                                        /calendar/capacity, /knowledge, /renegotiation)
```

The browser never sees the LiveKit secret. The worker is a **separate process**
from the FastAPI app and shares its brain only through HTTP, so voice and web
stay perfectly in sync with zero duplicated logic.

## What you need

- A **LiveKit** project (free at [cloud.livekit.io](https://cloud.livekit.io)) -
  gives you `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.
- A **Google AI Studio** API key (`GOOGLE_API_KEY`) with access to a Gemini Live
  native-audio model.
- The Clutch **API running** and reachable at `CLUTCH_API_BASE`.

Set the three LiveKit values on **both** the API (so it can mint tokens) and the
worker (so it can register).

## Setup & run

From the `backend/` directory:

```bash
python -m venv .venv-voice && source .venv-voice/bin/activate
pip install -r requirements-voice.txt
cp voice/.env.example .env   # then fill it in

python -m voice.agent download-files   # one-time: fetch Silero VAD weights
python -m voice.agent dev              # local dev (hot reload)
# or: python -m voice.agent start      # production
```

The worker uses **automatic dispatch** - it joins any room a participant
connects to, so no agent name or explicit dispatch is required. Open Crisis Mode
in the web app, allow the mic, and start talking.

## Docker

```bash
# from backend/
docker build -f voice/Dockerfile -t clutch-voice .
docker run --env-file .env clutch-voice
```

## The voice tool registry

| Tool | Calls | Purpose |
| --- | --- | --- |
| `assess_situation` | `POST /agent` | Full triage loop -> spoken survival plan |
| `get_commitments` | `GET /commitments` | Active commitments + status |
| `get_plan` | `GET /plan` | Feasibility, deficit, at-risk items |
| `get_capacity` | `GET /calendar/capacity` | Real focus time before deadlines |
| `consult_notes` | `POST /knowledge/search` | RAG over the user's briefs/specs |
| `draft_renegotiation` | `POST /renegotiation/draft` | Prepare a message (**draft only**) |

`draft_renegotiation` never sends - it only prepares a draft for one-tap review
in the web app, matching the human-in-the-loop guardrail everywhere else.

## Troubleshooting

- **Web app says voice is unavailable** - the API's `/voice/status` returns
  `enabled: false`. Set the three `LIVEKIT_*` values on the API and restart it.
- **Token request returns 503 mentioning livekit-api** - install
  `requirements-voice.txt` in the API's environment too (it provides the light
  `livekit-api` token dependency).
- **Worker connects but stays silent** - check `GOOGLE_API_KEY` and that the
  configured `GEMINI_LIVE_MODEL` is a native-audio model your key can access.
- **Agent answers but can't see your tasks** - confirm `CLUTCH_API_BASE` points
  at the running API and that CORS / network allow the worker to reach it.
