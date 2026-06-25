"""Clutch Voice Crisis Mode (Phase 8).

A standalone LiveKit Agents worker that lets you talk to Clutch hands-free:
\"Clutch, what do I do right now?\" It speaks through a Gemini Live native-audio
model and calls the same Clutch API the web app uses, so triage, planning and
renegotiation behave identically whether typed or spoken.

This package is intentionally separate from the FastAPI app: it runs as its own
process (python -m voice.agent dev) with its own heavy dependencies
(requirements-voice.txt).
"""
