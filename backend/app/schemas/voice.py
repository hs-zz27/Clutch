from pydantic import BaseModel


class VoiceTokenRequest(BaseModel):
    """Optional overrides; both default to the configured single-user room."""

    room: str | None = None
    identity: str | None = None


class VoiceTokenResponse(BaseModel):
    url: str
    token: str
    room: str
    identity: str


class VoiceStatusResponse(BaseModel):
    enabled: bool
    model: str
    voice: str
    room: str
