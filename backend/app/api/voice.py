"""Phase 8 - Voice Crisis Mode: room access tokens + a status probe.

The browser never sees the LiveKit API secret. It asks us for a short-lived
access token scoped to a single room; the voice agent worker (a separate
process) joins that same room and the two talk over WebRTC.

Voice is fully optional. If LiveKit isn't configured - or livekit-api isn't
installed - we return 503 so the UI degrades gracefully instead of the app
failing to import or start.
"""
import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.voice import (
    VoiceStatusResponse,
    VoiceTokenRequest,
    VoiceTokenResponse,
)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/status", response_model=VoiceStatusResponse)
def voice_status() -> VoiceStatusResponse:
    """Tell the frontend whether voice is available, without leaking secrets."""
    return VoiceStatusResponse(
        enabled=settings.voice_enabled,
        model=settings.GEMINI_LIVE_MODEL,
        voice=settings.GEMINI_LIVE_VOICE,
        room=settings.VOICE_ROOM_NAME,
    )


@router.post("/token", response_model=VoiceTokenResponse)
def create_voice_token(payload: VoiceTokenRequest) -> VoiceTokenResponse:
    """Mint a short-lived LiveKit access token for the browser to join a room."""
    if not settings.voice_enabled:
        raise HTTPException(
            status_code=503,
            detail=(
                "Voice Crisis Mode is not configured. Set LIVEKIT_URL, "
                "LIVEKIT_API_KEY and LIVEKIT_API_SECRET to enable it."
            ),
        )

    # Lazy import: the API still starts even if livekit-api isn't installed
    # (e.g. a minimal deploy that doesn't run voice).
    try:
        from livekit import api as lk_api
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail=(
                "livekit-api is not installed on the server. Install "
                "requirements-voice.txt to enable token minting."
            ),
        )

    room = payload.room or settings.VOICE_ROOM_NAME
    identity = payload.identity or f"user-{uuid.uuid4().hex[:8]}"

    try:
        token = (
            lk_api.AccessToken(
                settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET
            )
            .with_identity(identity)
            .with_name("Clutch user")
            .with_grants(
                lk_api.VideoGrants(
                    room_join=True,
                    room=room,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .with_ttl(timedelta(minutes=30))
            .to_jwt()
        )
    except Exception:
        raise HTTPException(
            status_code=502, detail="Failed to mint a voice access token."
        )

    return VoiceTokenResponse(
        url=settings.LIVEKIT_URL, token=token, room=room, identity=identity
    )
