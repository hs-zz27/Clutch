from datetime import datetime

from pydantic import BaseModel, Field

from app.models.renegotiation import OutboxStatus


class RenegotiationGenerateRequest(BaseModel):
    commitment_id: int
    tone: str = Field(
        default="professional and apologetic",
        description="Desired tone of the drafted message.",
    )


class RenegotiationUpdate(BaseModel):
    """Human edits to a draft before sending. All fields optional."""

    recipient: str | None = None
    subject: str | None = None
    body: str | None = None


class RenegotiationRead(BaseModel):
    id: int
    commitment_id: int
    recipient: str | None = None
    subject: str
    body: str
    status: OutboxStatus
    error: str | None = None
    created_at: datetime
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}
