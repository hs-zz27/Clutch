"""Runtime configuration for the Clutch voice worker.

The worker is a standalone process (not part of the FastAPI app), so it reads
its own environment. LiveKit credentials (LIVEKIT_URL / LIVEKIT_API_KEY /
LIVEKIT_API_SECRET) and the Google API key (GOOGLE_API_KEY) are consumed
directly by the LiveKit and Gemini plugins; here we only surface the few knobs
our own code touches.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Base URL of the running Clutch API. The worker calls it over HTTP so the
# voice agent reuses all planning / triage / renegotiation logic.
CLUTCH_API_BASE = os.getenv("CLUTCH_API_BASE", "http://localhost:8000").rstrip("/")

# Gemini Live model + prebuilt voice. Defaults mirror the API-side config.
GEMINI_LIVE_MODEL = os.getenv(
    "GEMINI_LIVE_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"
)
GEMINI_LIVE_VOICE = os.getenv("GEMINI_LIVE_VOICE", "Charon")

# Network timeout (seconds) for calls into the Clutch API. The /agent endpoint
# runs a multi-step LLM loop, so give it generous headroom.
API_TIMEOUT_SECONDS = float(os.getenv("CLUTCH_API_TIMEOUT", "90"))
