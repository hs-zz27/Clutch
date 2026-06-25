from datetime import datetime
from pydantic import BaseModel, Field


class StakeholderCreate(BaseModel):
    name: str
    relationship: str | None = None
    formality: int = Field(default=3, ge=1, le=5)
    notes: str | None = None


class StakeholderUpdate(BaseModel):
    name: str | None = None
    relationship: str | None = None
    formality: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class StakeholderRead(BaseModel):
    id: int
    name: str
    relationship: str | None
    formality: int
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
