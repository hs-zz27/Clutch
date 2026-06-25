from datetime import datetime
from pydantic import BaseModel, Field
from app.models.commitment import Status

class CommitmentCreate(BaseModel):
    title: str
    description: str | None = None
    deadline: datetime
    est_effort_minutes: int = Field(default=60, gt=0)        # expected (p50), positive
    effort_p80_minutes: int | None = Field(default=None, gt=0)  # worst-case (p80)
    importance: int = Field(default=3, ge=1, le=5)           # 1–5 only
    stakeholder: str | None = None
    min_viable_definition: str | None = None
    depends_on_id: int | None = None                         # prerequisite commitment

class CommitmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    deadline: datetime | None = None
    est_effort_minutes: int | None = Field(default=None, gt=0)
    effort_p80_minutes: int | None = Field(default=None, gt=0)
    importance: int | None = Field(default=None, ge=1, le=5)
    stakeholder: str | None = None
    min_viable_definition: str | None = None
    depends_on_id: int | None = None
    status: Status | None = None
    progress_pct: int | None = Field(default=None, ge=0, le=100)   # 0–100 only

class CommitmentRead(BaseModel):
    id: int
    title: str
    description: str | None
    deadline: datetime
    est_effort_minutes: int
    effort_p80_minutes: int | None
    importance: int
    stakeholder: str | None
    min_viable_definition: str | None
    depends_on_id: int | None
    status: Status
    progress_pct: int
    created_at: datetime

    model_config = {"from_attributes": True}
